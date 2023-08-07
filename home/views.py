import datetime
from django.views.generic import FormView
from .forms import ContactForm
from django.http import JsonResponse
from django.core.mail import send_mail



class Homepage(FormView):

    form_class = ContactForm
    template_name = 'home/home.html'
   
    # Add the year to the context (for the get)
    def get_context_data(self, **kwargs):
        kwargs = {'year' : datetime.date.today().year}
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
            # Currently unable to inform the modal it's invalid
            return self.form_invalid(form)