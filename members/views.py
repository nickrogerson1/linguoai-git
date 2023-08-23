from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.views.generic import UpdateView, DeleteView, FormView
from django import template
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.db.models import CharField, Value, QuerySet
from django.utils.html import escape

from .models import *
from .forms import *
from .api_funcs.ielts_score import *
from .api_funcs.corrections import find_difference
from .api_funcs.improved import improved_submission

import re, time
import statistics as stats
from decimal import Decimal

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes

from django.core.mail import send_mail
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from .tasks import *



# Costs per 1000 tokens
LLM_COSTS = {
    # up to 4k
'gpt-3' : {'input' :0.0015,
            'output': 0.002},
    # up to 8k
'gpt-4' : {'input': 0.03,
            'output': 0.06}
}


# Pricing per 100 words
PRICING = {
    'ielts_writing_task_2': {
        'USD': 0.09,
        'CNY': 0.7
    },
    'corrected_results': {
        'USD': 0.04,
        'CNY': 0.3
    },
    'improved_results': {
        'USD': 0.04,
        'CNY': 0.3
    }
}




class LoginUser(LoginView):
    redirect_authenticated_user = True
    form_class = LoginForm




from django.contrib.gis.geoip2 import GeoIP2
def get_country_code(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip =  x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    # Just return USA if it fails
    g = GeoIP2()
    try:
        return g.country_code(ip)
    except:
        return 'US'



class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )
account_activation_token = TokenGenerator()




class Registration(CreateView):

    form_class = SignUpForm
    template_name = 'members/home/register.html'

    def get(self, request):
        country_code = get_country_code(request)
    # Set the preferred currency to RMB when in China
        if country_code == 'CN':
            currency = 'CNY'
        else:
            currency = 'USD'

        form = SignUpForm(initial={'country': country_code, 'currency': currency})
        return render(request, self.template_name, {"form": form})
    

    def post(self, request):
        form = self.get_form()
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            self.send_activation_email(request, user)
            return render(request, 'registration/confirm_email.html', {'email' : user.email})
        else:
            self.object = ''
            return super().form_invalid(form)

    
    def send_activation_email(self, request, user):
            
            print(user.pk)
            message = render_to_string('registration/activate_account.html', {
                'name': user.first_name,
                'domain': 'localhost:8000',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
                # 'protocol': 'https' if request.is_secure() else 'http'
            })

            print(message)
            
            send_mail(
                'Activate your LinguoAI account.',
                message,
                '"Linguo AI" <activation@linguo.ai>',
                ['linguoaisite@gmail.com'],
                html_message = message
            ) 


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
       
        return redirect('activated')
    else:
        return HttpResponse('Activation link is invalid!')
    



# Password reset
class CustomPasswordResetView(PasswordResetView):
    form_class = PasswordResetEmail
    from_email = '"Linguo AI" <password-reset@linguo.ai>'
    html_email_template_name = 'registration/password_reset_email.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = PasswordResetPass



@login_required(login_url="/login/")
def index(request):
    user = request.user

    usage1 = IeltsWritingTask2.objects.filter(owner=user.id).values('charged', 'new_balance', 'time_created').annotate(usage_type=Value('Ielts Writing Task 2',output_field=CharField()))
    usage2 = CorrectedSubmission.objects.filter(owner=user.id).values('charged', 'new_balance', 'time_created').annotate(usage_type=Value('Corrected Submission',output_field=CharField()))
    usage3 = ImprovedSubmission.objects.filter(owner=user.id).values('charged', 'new_balance', 'time_created').annotate(usage_type=Value('Improved Submission',output_field=CharField()))
    usage = usage1.union(usage2,usage3).order_by('-time_created')


# Calculate data to use in chartjs
    days_ago = datetime.timedelta(days=15)
    today = datetime.datetime.today().date()
    time_ago = today - days_ago
    # print(time_ago)

    counted = {}

# Set up the days for the labels and set them to zero
    for days_ago in range(15):
        day = (today - datetime.timedelta(days=days_ago)).strftime('%d %b')
        counted[day] = 0

    for entry in usage:
        if entry['time_created'].date() <= time_ago:
            break
        else:
            date = entry['time_created'].date().strftime('%d %b')
            counted[date] += entry['charged']

    labels = ''
    data = ''
    
    for i,(k,v) in enumerate(reversed(counted.items())):
        if i < len(counted)-1:
            labels += k + ','; data += str(v) + ','
        else:
            labels += k; data += str(v)

    # Bring usage down to just ten
    usage = usage[:10]

    # Work out purchases
    purchases = PurchaseHistory.objects.filter(owner=user.id).values('amount', 'time_created').order_by('-time_created')[:10]

    currency = '$' if user.currency == 'USD' else '¥'
    return render(request, 'members/home/index.html', {'usage' : usage, 'labels' : labels, 'data' : data, 'purchases' : purchases, 'currency' : currency})



@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('members/home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('members/home/page-500.html')
        return HttpResponse(html_template.render(context, request))



class UpdateInfo(LoginRequiredMixin, UpdateView):
    model = User
    fields = '__all__'
    template_name = 'general/members/update.html'
    
    def get_success_url(self):
        return reverse('dashboard')

    # Override default to only allow current user to update
    def get_queryset(self):
        # qs = super(UpdateInfo, self).get_queryset()
        return super().get_queryset().filter(username=self.request.user)


class DeleteUser(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'general/members/update.html'

    def get_success_url(self):
        return reverse('register')
    


class InternalContactForm(FormView):

    form_class = ContactForm
    template_name = 'members/home/contact-form.html'

    # Homepage contact form 
    def post(self, request):
        form = self.get_form()
        if form.is_valid():
            user = request.user
            name = user.first_name
            email = user.email
            msg = request.POST['message'].replace('\n', '<br>')

            body = f'''
            This is to let you know the following email was sent
            internally from the LinguoAI site from:<br><br>
            Username: <strong>{user}</strong><br>
            Name: {name}<br>
            Email: {email}<br><br>
            {msg}<br><br>
            END OF MESSAGE
            '''

            send_mail(
                'Internal Email from LinguoAI',
                body,
                '"Linguo AI" <admin@linguo.ai>',
                ['linguoaisite@gmail.com'],
                html_message = body
            ) 

        # Add session variable to include their name
        # As can't pass any context in the redirect
            request.session['name'] = name  

            return redirect('message-success')
        else:
            return self.form_invalid(form)



class BalanceCheckMixin:

    def check_user_has_sufficient_funds(self, results_type, sub=None, q=None, a=None):

    # Check the cost before starting
        currency = self.request.user.currency
        price_per_100_words = PRICING[results_type]['USD'] if currency == 'USD' else PRICING[results_type]['CNY']

        if sub:
            total_words = len(sub.strip().split())
        else:
            total_words = len((q + ' ' + a).strip().split())

        cost = round((total_words / 100) * price_per_100_words, 2)

    # Enforce Minimum charge
        if currency == 'USD':
            charged = 0.05 if cost < 0.05 else cost
        else:
            # for CNY
            charged = 0.5 if cost < 0.5 else cost

        # Then make sure they have enough money
        if self.request.user.balance < charged:
            messages.warning(self.request, "Ooops, looks like you don't have enough credit to make that submission.")
            return False
        
        return [ price_per_100_words, total_words, charged ]




class ImprovedFormView(LoginRequiredMixin, BalanceCheckMixin, FormView):
    model = ImprovedSubmission
    template_name = 'members/home/input-form-general.html'
    form_class = ImprovedForm
    success_url = 'sent-successfully/'


    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
            print(request)
            return super(ImprovedFormView, self).get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')


    def post(self, request):
        t0 = time.time()
        form = ImprovedForm(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            t0 = time.time()
            sub = escape(self.object.submission)

            args = self.check_user_has_sufficient_funds('improved_results', sub=sub)

        # If they have insufficient funds, then end it
            if not args:
                return redirect('insufficient-funds')
            
            user_id = self.request.user.id
            
            # Then pass to Celery to process
            get_improved_results.delay(t0, user_id, sub, *args)
              
            return redirect(self.success_url)
        else:
            self.object = ''
            return super(ImprovedFormView, self).form_invalid(form)
        




class IeltsWritingTask2View(LoginRequiredMixin, BalanceCheckMixin, FormView):
    model = IeltsWritingTask2
    template_name = 'members/home/input-form-ielts-writing-task-2.html'
    form_class = IeltsWritingTask2Form
    success_url = 'sent-successfully/'
    extra_context = ''


    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
        # Add this to extra context as the form wipes out the kwargs being passed down
            if 'Firefox' in request.META['HTTP_USER_AGENT']:
                date = datetime.datetime.now().strftime("%B %Y")
                self.extra_context = {'browser': 'Firefox', 'date': date}
            return super().get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')


    def post(self, request):
        t0 = time.time()
        form = IeltsWritingTask2Form(request.POST)
        if form.is_valid():
            t0 = time.time()

            self.object = form.save(commit=False)
            q = escape(self.object.question)
            a = escape(self.object.answer)

            args = self.check_user_has_sufficient_funds('ielts_writing_task_2', q=q, a=a)

        # If they have insufficient funds, then end it
            if not args:
                return redirect('insufficient-funds')
            
            language = self.object.get_explanation_language_display().split(' ')[0]
            lang_code = self.object.explanation_language
            user_id = self.request.user.id

            get_ielts_writing_task_2_scores(t0, user_id, q, a, language, lang_code, *args)

            return redirect(self.success_url)
        else:
            self.object = ''
            return super(IeltsWritingTask2View, self).form_invalid(form)




class CorrectedFormView(LoginRequiredMixin, BalanceCheckMixin, FormView):
    model = CorrectedSubmission
    template_name = 'members/home/input-form-general.html'
    form_class = CorrectedForm
    success_url = 'sent-successfully/'


    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
            return super(CorrectedFormView, self).get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')


    def post(self, request):
        form = CorrectedForm(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            t0 = time.time()
            sub = escape(self.object.submission)

            args = self.check_user_has_sufficient_funds('corrected_results', sub=sub)

        # If they have insufficient funds, then end it
            if not args:
                return redirect('insufficient-funds')
            
            user_id = self.request.user.id
            
            # Then pass to Celery to process
            get_corrected_results.delay(t0, user_id, sub, *args)
              
            return redirect(self.success_url)
            
        else:
            self.object = ''
            return super(CorrectedFormView, self).form_invalid(form)



# Mixins for detail and list views
class DetailViewMixin:

    def get(self, request, pk):
        obj = self.model.objects.get(pk=pk)
        if obj.user_reported:
            values = obj.userreportedresults_set.latest('refunded', 'decision')
            # obj.refunded = values.refunded
            obj.decision = values.decision
            obj.symbol = '$' if request.user.currency == 'USD' else '¥'
        
        if self.model == CorrectedSubmission:
            sub = obj.submission
            result = obj.result
            obj.corrections = find_difference(sub, result)


        return render(request, self.template_name, {'result' : obj})


class ListViewQueryMixin:

    def get_queryset(self) -> QuerySet[any]:
        return self.model.objects.filter(owner=self.request.user.pk,user_deleted=False).order_by('-time_created')
    


# IELTS Task 2
class IeltsResultsView(LoginRequiredMixin, ListViewQueryMixin, ListView):
    model = IeltsWritingTask2
    paginate_by = 25
    template_name = 'members/home/ielts-writing-task-2-results.html'

# Add average band scores to list
# This happens after get_queryset, so no need to change it for user_deleted
    def get_context_data(self, **kwargs):
        context = super(IeltsResultsView, self).get_context_data(**kwargs)
        values = list(map(lambda x: float(x[0]), context['object_list'].values_list('band')))
        if values:
            context['mean_score'] = round(stats.mean(values), 1) 
            context['median_score'] = stats.median(values)
        return context
        
class IeltsResultsDetailView(LoginRequiredMixin, DetailViewMixin, DetailView):
    model = IeltsWritingTask2
    template_name = 'members/home/ielts-writing-task-2-success.html'
    context_object_name = 'result'



# Corrected Results
class CorrectedResultsView(LoginRequiredMixin, ListViewQueryMixin, ListView):
    model = CorrectedSubmission
    paginate_by = 25
    template_name = 'members/home/general-results.html'


# This is so as not to make multiple templates
    def get_context_data(self, **kwargs):
        context = super(CorrectedResultsView, self).get_context_data(**kwargs)
        context['corrected'] = True
        context['detail'] = 'corrected-results-detail'

        return context
    

class CorrectedResultsDetailView(LoginRequiredMixin, DetailViewMixin, DetailView):
    model = CorrectedSubmission
    template_name = 'members/home/corrected-form-success.html'
    context_object_name = 'result'



# Improved results
class ImprovedResultsView(LoginRequiredMixin, ListViewQueryMixin, ListView):
    model = ImprovedSubmission
    paginate_by = 25
    template_name = 'members/home/general-results.html'

    def get_context_data(self, **kwargs):
        context = super(ImprovedResultsView, self).get_context_data(**kwargs)
        context['detail'] = 'improved-results-detail'
        return context

class ImprovedResultsDetailView(LoginRequiredMixin, DetailViewMixin, DetailView):
    model = ImprovedSubmission
    template_name = 'members/home/improved-form-success.html'
    context_object_name = 'result'




# Need to do some of check to add submissions that are incomplete to the top of the list
class ResultsLogView(LoginRequiredMixin, ListView):

    paginate_by = 25
    template_name = 'members/home/log.html'

    def get_queryset(self) -> QuerySet[any]:
        id = self.request.user.id
        # (Download Checkbox) Submission Type - Time Submitted - Status (Complete/Being Processed/Failed)
        usage1 = (IeltsWritingTask2.objects.filter(owner=id,user_deleted=False).values('pk', 'time_created')
            .annotate(type=Value('Ielts Writing Task 2'), url_link=Value('ielts-writing-task-2-results-detail')))
        usage2 = (CorrectedSubmission.objects.filter(owner=id,user_deleted=False).values('pk', 'time_created')
            .annotate(type=Value('Corrected Submission'), url_link=Value('corrected-results-detail')))
        usage3 = (ImprovedSubmission.objects.filter(owner=id,user_deleted=False).values('pk', 'time_created')
            .annotate(type=Value('Improved Submission'), url_link=Value('improved-results-detail')))
        return usage1.union(usage2,usage3).order_by('-time_created')




class UserDeleteMixin(View):
# Deletes the object just for the User and NOT the backend
    def post(self, request):
        if request.method == "POST":
            print(f'VAR: {self.request.POST.getlist("checks")}')

            try:
                count = len(self.request.POST.getlist("checks"))
                self.model.objects.filter(
                pk__in=self.request.POST.getlist('checks'), 
        #Make sure they haven't messed about with the HTML and it's theirs
                owner=request.user.id 
                ).update(user_deleted = True)

                msg = ' was' if count == 1 else  's were'
                messages.success(request, f'Your selected submission{msg} successfully removed.')
            except:
                messages.error(request, 'Operation failed!')

            return redirect(reverse(self.success_url))
        
class CorrectedDeleteFiles(UserDeleteMixin):
    template_name = 'members/home/corrected-form-success.html'
    model = CorrectedSubmission
    success_url = 'corrected-results'

class ImprovedDeleteFiles(UserDeleteMixin):
    template_name = 'members/home/improved-form-success.html'
    model = ImprovedSubmission
    success_url = 'improved-results'

class IeltsWritingTask2DeleteFiles(UserDeleteMixin):
    template_name = 'members/home/ieltswriting-task-2-success.html'
    model = IeltsWritingTask2
    success_url = 'ielts-writing-task-2-results'


class LogDeleteFiles(View):
    template_name = 'members/home/log.html'
    success_url = 'log'

    def post(self, request):
        if request.method == "POST":
            print(f'VAR: {self.request.POST.getlist("checks")}')

            try:
                items = request.POST.getlist("checks")

                for i,item in enumerate(items):
                    model = item.split('/')[0]
                    pk = item.split('/')[1]

                    if model.startswith('improved'):
                        model = ImprovedSubmission
                    elif model.startswith('corrected'):
                        model = CorrectedSubmission
                    else:
                        model = IeltsWritingTask2

                    model.objects.filter(pk=pk,
            #Make sure they haven't messed about with the HTML and it's theirs
                    owner=request.user.id 
                    ).update(user_deleted=True)

                msg = 's were' if i else ' was'
                messages.success(request, f'Your selected submission{msg} successfully removed.')
            except:
                messages.error(request, 'Operation failed!')

            return redirect(reverse(self.success_url))



def report_bad_result(request, url):

    if request.method == "POST":
        # form = ReportForm(request.POST)
        # if form.is_valid():

        user = request.user
        name = user.first_name
        email = user.email
        msg = request.POST['message'].replace('\n', '<br>')

        path = url.split('/')
        model = path[1]
        pk = path[2]
        
        if model == 'corrected-results':
            sub = CorrectedSubmission.objects.get(pk=pk)
            r = UserReportedResults(reason=msg, corrected=sub, owner=user)
        elif model == 'improved-results':
            sub = ImprovedSubmission.objects.get(pk=pk)
            r = UserReportedResults(reason=msg, improved=sub, owner=user)
        else:
            sub = IeltsWritingTask2.objects.get(pk=pk)
            r = UserReportedResults(reason=msg, ielts_writing_task_2=sub, owner=user)

        sub.user_reported = True
        sub.save()
        r.save()

# Work out their reporting form
        total_subs = user.total_submissions
        new_reports = user.reports + 1
        new_percent_reported = (new_reports / total_subs) * 100

        user.reports = new_reports
        user.percent_reported = new_percent_reported
        user.save()

        body = f'''
            This is to let you know that a bad result has been reported and needs to be checked.
            <br><br>
            This report was made by <strong>{name}</strong> whose email is {email}:
            <br><br>
            {msg}
            <br><br>
            END OF MESSAGE
            '''

        # send_mail(
        #     'Bad Result Reported',
        #     body,
        #     '"Linguo AI" <admin@linguo.ai>',
        #     ['linguoaisite@gmail.com'],
        #     html_message = body
        #     )   
        

        # Tell the modal it can close
        return JsonResponse({'report_success' : True}, status = 200)
        
        print('didn\t work')



def get_bulk_pdf_task(request, pks, type=None):
    sub_type = request.path.split('/')[1]
    user = request.user.username
    get_bulk_pdf.delay(sub_type, user, pks, type=type)
    messages.success(request, 'We will process your PDFs as fast as we can.')
    return redirect(reverse('corrected-results'))


def get_bulk_mixed_pdf_task(request, url_str):
    get_bulk_mixed_pdf.delay(request, url_str)