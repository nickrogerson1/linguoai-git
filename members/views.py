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


from io import BytesIO
import docx
from striprtf.striprtf import rtf_to_text
import fitz
from zipfile import ZipFile
import redis


from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import environ
env = environ.Env()
environ.Env.read_env()

r = redis.Redis(host=env('REDISHOST'), port=env('REDISPORT'),username="default", password=env('REDISPASSWORD'))

from .pricing import *


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

    def check_user_has_sufficient_funds(self, results_type, sub=None, q=None, a=None, multi=False):

        TWO_PLACES = Decimal("0.01")

    # Check the cost before starting
        user = self.request.user.username
        currency = self.request.user.currency
        price_per_100_words = PRICING[results_type]['USD'] if currency == 'USD' else PRICING[results_type]['CNY']

        if sub:
            total_words = len(sub.strip().split())
        else:
            total_words = len((q + ' ' + a).strip().split())

        cost = Decimal(round((total_words / 100) * price_per_100_words, 2)).quantize(TWO_PLACES)

    # Enforce Minimum charge
        if currency == 'USD':
            charged = Decimal(MIN_CHARGE['USD']).quantize(TWO_PLACES) if cost < Decimal(MIN_CHARGE['USD']).quantize(TWO_PLACES) else cost
        else:
            # for CNY
            charged = Decimal(MIN_CHARGE['CNY']).quantize(TWO_PLACES) if cost < Decimal(MIN_CHARGE['CNY']).quantize(TWO_PLACES) else cost

        temp_balance = None
        
        if multi:
            # r = redis.Redis()
            with r.lock('user_balance'):
                temp_balance = r.hget(user, 'temp_balance')

        print(f'REQ BALANCE: {type(self.request.user.balance)}')

        user_balance = Decimal(float(temp_balance)).quantize(TWO_PLACES) if temp_balance else self.request.user.balance
        print(f'TEMP BALANCE {temp_balance}')
        print(f'USER BALANCE: {user_balance}')

        # If they don't have enough money:
        if user_balance < charged:
            if multi:
                return [ price_per_100_words, total_words, charged, 'Rejected: Insufficient Funds']
            else:
            # Only send warning when redirecting
                messages.warning(self.request, "Ooops, looks like you don't have enough credit to make that submission.")
                return False
        
        # Otherwise reduce temp_balance
        if multi:
            with r.lock('user_balance'):
                user_balance = float(user_balance - charged)
                print(f'599 - {type(user_balance)}')
                r.hset(user, mapping={'temp_balance' : user_balance})
                return [ price_per_100_words, total_words, charged, 'Awaiting Response' ]
            
        return [ price_per_100_words, total_words, charged ]

class StandardSubMixin:

    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
            return super().get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')

    def get_context_data(self):
        price = PRICING[self.charge_type]['USD']/100 if self.request.user.currency == 'USD' else PRICING[self.charge_type]['CNY']/100
        min_charge = MIN_CHARGE['USD'] if self.request.user.currency == 'USD' else MIN_CHARGE['CNY']
        min_words = int(min_charge / price)
        symbol = '$' if self.request.user.currency == 'USD' else '¥'
        kwargs = {'per_word' : symbol + str(price), 'min_charge' : symbol + f'{min_charge:.2f}', 'min_words' : min_words }
        return super().get_context_data(**kwargs)
    
    # def post(self, request):
    #     form = CorrectedForm(request.POST)
    #     if form.is_valid():
    #         self.object = form.save(commit=False)

    #         t0 = time.time()
    #         sub = escape(self.object.submission)

    #         args = self.check_user_has_sufficient_funds(self.charge_type, sub=sub)
    #          # [ price_per_100_words, total_words, charged ]

    #     # If they have insufficient funds, then end it
    #         if not args:
    #             return redirect('insufficient-funds')
            
    #         user_id = self.request.user.id
    #         username = self.request.user.username
    #         symbol = '$' if self.request.user.currency == 'USD' else '¥'
    #     # Only one submission so must be 1
    #         html_id = 1
            
    #         # Then pass to Celery to process
    #         get_results.delay(t0, username, user_id, sub, html_id, model, *args)
              
    #         # return redirect(self.success_url)
    #         ctx = {'word_count' : args[1], 'cost' : args[2], 'sub_type' : self.sub_type, 'symbol' : symbol}
    #         return render(request, "members/home/sent-success.html", context=ctx)
            
    #     else:
    #         self.object = ''
    #         return super(CorrectedFormView, self).form_invalid(form)




class IeltsWritingTask2View(LoginRequiredMixin, BalanceCheckMixin, FormView):
    model = IeltsWritingTask2
    template_name = 'members/home/input-form-ielts-writing-task-2.html'
    form_class = IeltsWritingTask2Form
    charge_type = 'ielts_writing_task_2'
    success_url = 'submitted/'

    def get(self, request, *args, **kwargs):
        # If they have some balance
        if self.request.user.balance:
            return super().get(self, request, *args, **kwargs)
        else:
        # Otherwise redirect to top up page
            return redirect('insufficient-funds')

    def get_context_data(self):
        price = PRICING[self.charge_type]['USD']/100 if self.request.user.currency == 'USD' else PRICING[self.charge_type]['CNY']/100
        min_flat_rate = 250 * price
        symbol = '$' if self.request.user.currency == 'USD' else '¥'
        kwargs = {'per_word' : symbol + str(price), 'min_flat_rate' : symbol + f'{min_flat_rate:.2f}'}
        return super().get_context_data(**kwargs)


    # def post(self, request):
    #     t0 = time.time()
    #     form = IeltsWritingTask2Form(request.POST)
    #     if form.is_valid():

    #         self.object = form.save(commit=False)
    #         q = escape(self.object.question)
    #         a = escape(self.object.answer)

    #         args = self.check_user_has_sufficient_funds('ielts_writing_task_2', q=q, a=a)

    #     # If they have insufficient funds, then end it
    #         if not args:
    #             return redirect('insufficient-funds')
            
    #         language = self.object.get_explanation_language_display().split(' ')[0]
    #         lang_code = self.object.explanation_language
    #         username = self.request.user.username
    #         user_id = self.request.user.id

    #         get_ielts_writing_task_2_scores(t0, username, user_id, q, a, language, lang_code, *args)

    #         return redirect(self.success_url)
    #     else:
    #         self.object = ''
    #         return super(IeltsWritingTask2View, self).form_invalid(form)
        
    def post(self, request):
        t0 = time.time()
        form = IeltsWritingTask2Form(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            q = escape(self.object.question)
            a = escape(self.object.answer)

            args = self.check_user_has_sufficient_funds('ielts_writing_task_2', q=q, a=a)
            # [ price_per_100_words, total_words, charged ]

        # If they have insufficient funds, then end it
            if not args:
                return redirect('insufficient-funds')
            

            language = self.object.get_explanation_language_display().split(' ')[0]
            lang_code = self.object.explanation_language
            username = self.request.user.username
            user_id = self.request.user.id
            symbol = '$' if self.request.user.currency == 'USD' else '¥'
        # Only one submission so must be 1
            html_id = 1
            
            # Then pass to Celery to process
            get_ielts_writing_task_2_scores(t0, username, user_id, q, a, language, lang_code, html_id, *args)
            
            # return redirect(self.success_url)
            ctx = {'word_count' : args[1], 'cost' : args[2], 'sub_type' : self.sub_type, 'symbol' : symbol}
            return render(request, "members/home/sent-success.html", context=ctx)
        else:
            self.object = ''
            return super(ImprovedFormView, self).form_invalid(form)
            




class ImprovedFormView(LoginRequiredMixin, BalanceCheckMixin, StandardSubMixin, FormView):
    model = ImprovedSubmission
    template_name = 'members/home/input-form-general.html'
    form_class = ImprovedForm
    charge_type = 'improved_results'
    sub_type = 'Improved'


    def post(self, request):
        t0 = time.time()
        form = ImprovedForm(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            t0 = time.time()
            sub = escape(self.object.submission)

            args = self.check_user_has_sufficient_funds(self.charge_type, sub=sub)
             # [ price_per_100_words, total_words, charged ]

        # If they have insufficient funds, then end it
            if not args:
                return redirect('insufficient-funds')
            
            user_id = self.request.user.id
            username = self.request.user.username
            symbol = '$' if self.request.user.currency == 'USD' else '¥'
        # Only one submission so must be 1
            html_id = 1
            
            # Then pass to Celery to process
            get_improved_results.delay(t0, username, user_id, sub, html_id, *args)
              
            # return redirect(self.success_url)
            ctx = {'word_count' : args[1], 'cost' : args[2], 'sub_type' : self.sub_type, 'symbol' : symbol}
            return render(request, "members/home/sent-success.html", context=ctx)
        else:
            self.object = ''
            return super(ImprovedFormView, self).form_invalid(form)
        




class CorrectedFormView(LoginRequiredMixin, BalanceCheckMixin, StandardSubMixin, FormView):
    model = CorrectedSubmission
    template_name = 'members/home/input-form-general.html'
    form_class = CorrectedForm
    charge_type = 'corrected_results'
    sub_type = 'Corrected'


    def post(self, request):
        form = CorrectedForm(request.POST)
        if form.is_valid():
            self.object = form.save(commit=False)

            t0 = time.time()
            sub = escape(self.object.submission)

            args = self.check_user_has_sufficient_funds(self.charge_type, sub=sub)
             # [ price_per_100_words, total_words, charged ]

        # If they have insufficient funds, then end it
            if not args:
                return redirect('insufficient-funds')
            
            user_id = self.request.user.id
            username = self.request.user.username
            symbol = '$' if self.request.user.currency == 'USD' else '¥'
        # Only one submission so must be 1
            html_id = 1
            
            # Then pass to Celery to process
            get_corrected_results.delay(t0, username, user_id, sub, html_id, *args)
              
            # return redirect(self.success_url)
            ctx = {'word_count' : args[1], 'cost' : args[2], 'sub_type' : self.sub_type, 'symbol' : symbol}
            return render(request, "members/home/sent-success.html", context=ctx)
            
        else:
            self.object = ''
            return super(CorrectedFormView, self).form_invalid(form)







class FileFieldFormView(LoginRequiredMixin,BalanceCheckMixin,FormView):
    
    form_class = FileFieldForm
    template_name = 'members/home/input-form-general.html'
    success_url = 'upload-success.html' 
    

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            t0 = time.time()
            return self.form_valid(form, t0)
        else:
            return self.form_invalid(form)

    def form_valid(self, form, t0):

        file = self.request.FILES['file']
        file_type = file.content_type
        # print(file_type)
        if file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            sub = self.get_docx_text(file)
            res = self.process_text(t0, sub)            

        elif file_type == 'application/pdf': 
            sub = self.get_pdf_text(file)
            res = self.process_text(t0, sub)

        elif file_type == 'text/rtf':
            sub = self.get_rtf_text(file)
            res = self.process_text(t0, sub)

        elif file_type == 'text/plain':
            sub = self.get_txt_text(file)
            res = self.process_text(t0, sub)

        elif file_type == 'application/zip':
            subs = self.unzip_files(file)
            for s in subs:
        # Keep track of cost as this processes
            # s[0] sub & s[1] filename
                print(f'VAR: {s}')
                res = self.process_text(t0, s[0], s[1])
            # Pass them straight through to Celery
                # get_corrected_results.delay(t0, user_id, s[0], *res)
                
                print(s)

# Handle folders that aren't zipped
        # elif file_type == 'application/octet-stream':
        #     for f in file:
        #         f = BytesIO(f)
        #         print(f)
        #         return self.form_valid(f)

        else:
            print(f"Can't open file type: {file_type}")

        print(f'RES {res}')
        
        # Then pass to Celery to process (not zips)
        # if file_type != 'application/zip':
            # get_corrected_results.delay(t0, user_id, sub, *res)
            
        # return redirect(self.success_url)
        return super().form_valid(form)





# Update IELTS form so that it has a waiting page like improved and corrected

# Make sure data gets sanitised

# Finish wiring up PDFs
# (Reinstall Redis and) upload to Railway with Daphne and see it still works


        
    
    def process_text(self, t0, sub, file_name=None):
        args = self.check_user_has_sufficient_funds('corrected_results', sub=sub, multi=True)
        # [ price_per_100_words, total_words, charged ]

        print(f'ARGS: {args}')
# Insufficient Funds
    # Reject if over 5000 words
        if args[1] >= 5000:
            args[3] = 'Rejected: Submit content less than 5000 words in length'
      
        file_name = file_name if file_name else self.request.FILES['file'].name
        username = self.request.user.username
        user_id = self.request.user.id

    # Increase the id by 1 each time
        id = r.hincrby(username,'num')
        print(f'ID: {id}')    
        curr = '$' if self.request.user.currency == 'USD' else '¥'
        
        # print(f'USER: {self.request.user.username}')
        channel_name = r.hget(username, 'channel').decode()
        if channel_name:
            channel_layer = get_channel_layer()
            
        async_to_sync(channel_layer.send)(channel_name, {
                'type': 'update',
                'wordCount': args[1],
                'cost': f'{curr}{args[2]}',
                'fileName': file_name,
                'id' : id,
                'status': args[3],
            })
        
        
        
    # Only process if awaiting response, otherwise reject via ws and do nothing
        if args[3] == 'Awaiting Response':
            #Remove 'insufficient funds' info from args before passing through
            args.pop()
            if 'corrected' in self.request.path_info:
                get_corrected_results.delay(t0, username, user_id, sub, id, *args)
            else:
                get_improved_results.delay(t0, username, user_id, sub, id, *args)
        
        # return [id, *args]
        
  
    def get_docx_text(self, file):
        doc = docx.Document(file)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        final = '\n'.join(fullText)
        print(final)
        return final
    

    def get_pdf_text(self, file):

        if isinstance(file, bytes):
        # Zipped files don't need to be read
            b = BytesIO(file)
        else:
            b = BytesIO(file.read())
        with fitz.open('pdf',b) as doc:
            text = ""
            for page in doc:
        # Produces weird unicode so needs replacing
                text += page.get_text().replace('�', ' ')
        print(text)
        return text


    def get_rtf_text(self, file):
        text = rtf_to_text(file.read().decode())
        print(text)
        return text
    

    def get_txt_text(self, file):
        text = ''
        for line in file:
            text += line.decode()
        print(text)
        return text


    def unzip_files(self, input_zip):
        input_zip = ZipFile(input_zip)
        all_zips = []
        for name in input_zip.namelist():
            print(name)
            if name.endswith('docx'):
                txt = self.get_docx_text(BytesIO(input_zip.read(name)))

            elif name.endswith('pdf'): 
                txt = self.get_pdf_text(input_zip.read(name))

            elif name.endswith('rtf'):
                txt = rtf_to_text(input_zip.read(name).decode())

            elif name.endswith('txt'):
                txt = input_zip.read(name).decode()

            else:
                return "You've submitted a file that can't be processed."
            all_zips.append((txt,f'{name} [ZIPPED]'))
        return all_zips




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
   
    

    def get_queryset(self):
        
        r = self.request
        id = self.request.user.id
        # (Download Checkbox) Submission Type - Time Submitted - Status (Complete/Being Processed/Failed)
        usage1 = (IeltsWritingTask2.objects.filter(owner=id,user_deleted=False).values('pk', 'time_created')
            .annotate(type=Value('Ielts Writing Task 2'), url_link=Value('ielts-writing-task-2-results-detail'), status=Value('Completed')))
        usage2 = (CorrectedSubmission.objects.filter(owner=id,user_deleted=False).values('pk', 'time_created')
            .annotate(type=Value('Corrected Submission'), url_link=Value('corrected-results-detail'), status=Value('Completed')))
        usage3 = (ImprovedSubmission.objects.filter(owner=id,user_deleted=False).values('pk', 'time_created')
            .annotate(type=Value('Improved Submission'), url_link=Value('improved-results-detail'), status=Value('Completed')))
        
        sorted_results = usage1.union(usage2,usage3).order_by('-time_created')
        # print(sorted_results)
        
        # Add in whatever was submitted
        format = {
            'pk' : 'NA',
            'time_created' : 'In Progress',
            'type' : 'Whatever it is',
            'url_link' : None,
            'status' : 'Pending'
        }

        print(f'Request: {r.path}')

        return sorted_results



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