from django.shortcuts import render
import datetime
from django.views.generic import FormView
from .forms import ContactForm
from django.http import JsonResponse
from django.core.mail import send_mail

# Handles issue of importing from another folder/app
import sys
sys.path.append('.')
from members.pricing import *



class Homepage(FormView):

    form_class = ContactForm
    template_name = 'home/home.html'
   
    # Add the year to the context (for the get)
    def get_context_data(self, **kwargs):
        # Dynamically send over the pricing
        ielts_writing_task_2 = PRICING['ielts_writing_task_2']
        ielts_usd = ielts_writing_task_2['USD']
        ielts_cny = ielts_writing_task_2['CNY']
        corrected = PRICING['corrected_results']
        corrected_usd = corrected['USD']
        corrected_cny = corrected['CNY']
        improved = PRICING['improved_results']
        improved_usd = improved['USD']
        improved_cny = improved['CNY']

        kwargs = {'year' : datetime.date.today().year,
                  'ielts_usd' : ielts_usd,
                  'ielts_cny' : ielts_cny,
                  'corrected_usd' : corrected_usd,
                  'corrected_cny' : corrected_cny,
                  'improved_usd' : improved_usd,
                  'improved_cny' : improved_cny  
            }
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        print(kwargs)
        return super().get_context_data(**kwargs)

    # Homepage contact form 
    def post(self, request):
        form = self.get_form()
        if form.is_valid():
            name = request.POST['name']
            email = request.POST['email']
            msg = request.POST['message'].replace('\n', '<br>')

            body = f'''
            This is to let you know the following email was sent from the LinguoAI homepage
            from <strong>{name}</strong> whose email is {email}:
            <br><br>
            {msg}
            <br><br>
            END OF MESSAGE
            '''

            send_mail(
                'Email from LinguoAI Homepage',
                body,
                '"Linguo AI" <admin@linguo.ai>',
                ['linguoaisite@gmail.com'],
                html_message = body
            )   

            # Tell the modal it can close
            return JsonResponse({'formSubmitSuccess' : True}, status = 200)
        else:
            # Currently unable to inform the modal it's invalid so done with JS
            return self.form_invalid(form)