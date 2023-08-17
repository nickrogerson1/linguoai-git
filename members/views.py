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
        'USD': 0.08,
        'CNY': 0.7
    },
    'corrected_results': {
        'USD': 0.03,
        'CNY': 0.3
    },
    'improved_results': {
        'USD': 0.03,
        'CNY': 0.3
    }
}



def get_country_code(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip =  x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    # Just return USA if it fails
    g = GeoIP2()
    try:
        return g.country_code(ip)
    except:
        return 'US'


class LoginUser(LoginView):
    redirect_authenticated_user = True
    form_class = LoginForm



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
    


from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

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


# This is to add the context to the data in the template context
# Can't override  get_context_data directly as it's being used by the GET method.
class ContextMixin:

    def get_context_data_post(self, data, start_time, price, total_words, charged, submission, answer=False):
    # Add all the openai data to the db
        # [html, model, prompt_tokens, completion_tokens, total_tokens]
        self.object.model_used = data[1]
        self.object.prompt_tokens = data[2]
        self.object.completion_tokens = data[3]
        self.object.total_tokens = data[4]
        
        # Get the current authenticated user
        user = self.request.user

        # Add them to the current db
        self.object.owner = user

         # Record the time it took
        t1 = time.time()
        self.object.processing_time = round(t1 -start_time, 3)
        
        if data[1].startswith('gpt-3'):
            model_used = 'gpt-3'
        elif data[1].startswith('gpt-4'):
            model_used = 'gpt-4'

        # Work out cost
        cost = round((data[2] / 1000) * LLM_COSTS[model_used]['input'] + (data[3] / 1000) * LLM_COSTS[model_used]['output'], 4)

        # Enforce minimum charge
        if user.currency == 'USD':
            if charged < 0.05:
                charged = 0.05
        # And for RMB
        else:
            if charged < 0.5:
                charged = 0.5

    # Save charged before continuing to make USD calculations
        self.object.charged = charged

    # Deduct the amount from their balance and add total submission
    # Do this here before converted into dollars
        u = User.objects.get(pk=user.id)
        u.balance -= Decimal(charged)
        u.total_submissions += 1
        u.save()

        self.object.new_balance = u.balance

    # Get the charges into dollars to make USD calculations
        usd_exchange_rate = 1

        if user.currency == 'CNY':
            usd_exchange_rate = 0.14
            charged = charged * usd_exchange_rate
        # Add this to the db to make it more coherent
            self.object.usd_charge = charged

        profit = charged - cost
        margin = round((profit / cost) * 100, 3)

        print(f'Exchange rate: {usd_exchange_rate}')

        # Then save them
        self.object.currency = user.currency
        self.object.cost = cost
        self.object.total_words = total_words
        self.object.price_per_100_words = price
        self.object.usd_exchange_rate = usd_exchange_rate
        self.object.profit = profit
        self.object.margin = margin
        self.object.save()


        # Context only info
        # Let the template know this was a new search and not a lookup
        self.object.new_search = True
        self.object.symbol = '$' if user.currency == 'USD' else '¥'
        self.object.balance = Decimal(u.balance).quantize(Decimal('0.01'))

        # self.object.pk = self.object.pk

        ctx = {'result' : self.object}
        return ctx



class IeltsWritingTask2View(LoginRequiredMixin,ContextMixin,CreateView):
    model = IeltsWritingTask2
    template_name = 'members/home/input-form-ielts-writing-task-2.html'
    form_class = IeltsWritingTask2Form
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


# Override the entire post method and return to same page and ignore success_url
    def post(self, request, *args, **kwargs):
        t0 = time.time()
        form = IeltsWritingTask2Form(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)
            q = escape(self.object.question)
            a = escape(self.object.answer)


            # Check the cost before starting
            price_per_100_words = PRICING['ielts_writing_task_2']['USD'] if request.user.currency == 'USD' else PRICING['ielts_writing_task_2']['CNY']
            total_words = len((q + ' ' + a).strip().split())
            charged = round((total_words / 100) * price_per_100_words, 2)

            # Then make sure they have enough money
            if self.request.user.balance < charged:
                request.session['out_of_credit'] = True
                return redirect('insufficient-funds')


            t0 = time.time()
            q = escape(self.object.question)
            a = escape(self.object.answer)
            language = self.object.get_explanation_language_display().split(' ')[0]


            # Add all the openai data to the db
            # [html, model, prompt_tokens, completion_tokens, total_tokens]
            data = get_ielts_writing_task_2_score(q,a,language)
            if data:

                # Pull out the band and replace it with nothing
                reg = r'%%%%%([a-zA-Z0-9_\. ]+)%%%%%'
                m = re.search(reg, data[0], flags=re.I)
                self.object.band = m.group(1).replace('Band ', '')

                # Remove \n and change to <br>
                self.object.question = q.replace('\n', '<br>')
                self.object.answer = a.replace('\n', '<br>')
                # Get rid of first two breaks as well for admin interface
                score = re.sub(reg, '', data[0])
                self.object.score_res = score.replace('\n', '<br>').replace('<br>','',2)

                ctx = self.get_context_data_post(data, t0, price_per_100_words, total_words, charged, q, a)

                # Add the report url to the context
                ctx['result'].report_url = f'/ielts-writing-task-2/{ctx["result"].pk}/'
                ctx['link'] = 'ielts-writing-task-2'

                return render(request, 'members/home/ielts-writing-task-2-success.html', ctx)
            else:
                return redirect('unavailable')
        else:
            self.object = ''
            return super(IeltsWritingTask2View, self).form_invalid(form)




class CorrectedFormView(LoginRequiredMixin,ContextMixin, CreateView):
    model = CorrectedSubmission
    template_name = 'members/home/input-form-general.html'
    form_class = CorrectedForm


    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
            return super(CorrectedFormView, self).get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')

# Override the entire post method and return to same page and ignore success_url
    def post(self, request, *args, **kwargs):
        form = CorrectedForm(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            t0 = time.time()
            sub = escape(self.object.submission)

            # Check the cost before starting
            price_per_100_words = PRICING['corrected_results']['USD'] if request.user.currency == 'USD' else PRICING['corrected_results']['CNY']
            print(f'User Currency: {request.user.currency}')
            total_words = len(sub.strip().split())
            charged = round((total_words / 100) * price_per_100_words, 2)

            # Then make sure they have enough money
            if self.request.user.balance < charged:
                request.session['out_of_credit'] = True
                return redirect('insufficient-funds')
            
            data = call_and_find_difference(sub)

            if data:
                self.object.result = data[0].replace('\n', '').lstrip()

                ctx = self.get_context_data_post(data, t0, price_per_100_words, total_words, charged, sub)

            # More context
                self.object.corrections = data[5].replace('\n', '').lstrip()
                ctx['result'].report_url = f'/corrected-results/{ctx["result"].pk}/'
                ctx['link'] = 'corrected'
              
                return render(request, 'members/home/corrected-form-success.html', ctx)
            else:
                return redirect('unavailable')
        else:
            self.object = ''
            return super(CorrectedFormView, self).form_invalid(form)





class ImprovedFormView(LoginRequiredMixin,ContextMixin,CreateView):
    model = ImprovedSubmission
    template_name = 'members/home/input-form-general.html'
    form_class = ImprovedForm


    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
            print(request)
            return super(ImprovedFormView, self).get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')


# Overrirde the entire post method and return to same page and ignore success_url
    def post(self, request, *args, **kwargs):
        t0 = time.time()
        form = ImprovedForm(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            t0 = time.time()
            sub = escape(self.object.submission).replace('\n', '<br>')

            # Check the cost before starting
            price_per_100_words = PRICING['improved_results']['USD'] if request.user.currency == 'USD' else PRICING['improved_results']['CNY']
            total_words = len(sub.strip().split())
            charged = round((total_words / 100) * price_per_100_words, 2)

            # Then make sure they have enough money
            if self.request.user.balance < charged:
                request.session['out_of_credit'] = True
                return redirect('insufficient-funds')
            

            self.object.submission = sub
            data = improved_submission(sub)
            if data:
                self.object.improved_sub = data[0].replace('\n', '<br>')

                ctx = self.get_context_data_post(data, t0, price_per_100_words, total_words, charged, sub)

                # Add the report url to the context
                ctx['result'].report_url = f'/improved-results/{ctx["result"].pk}/'
                
                return render(request, 'members/home/improved-form-success.html', ctx)
            else:
                return redirect('unavailable')
        else:
            self.object = ''
            return super(ImprovedFormView, self).form_invalid(form)
        

# ***********************LIST AND DETAIL VIEWS********************************

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