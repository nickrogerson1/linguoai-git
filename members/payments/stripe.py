from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.views import View
from ..models import PurchaseHistory, User

from decimal import Decimal
import json
import stripe
import environ

env = environ.Env()
env.read_env(env.str('ENV_PATH','.env'))
stripe.api_key = env('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_API_KEY')


class CreateStripeCheckoutSessionView(View):
    """
    Create a checkout session and redirect the user to Stripe's checkout page
    """
    def post(self, request, *args, **kwargs):

    # Work out payment currency to set prices
        currency = request.user.currency

        if currency == 'USD':
            price = 'price_1NbM6eJmKGYbAOrbl3DJ7psO'
            payment_method_types = ['card']
            payment_method_options= {}
        else:
        # It's RMB
            price = 'price_1NbMIZJmKGYbAOrbExd6jv5z'
            payment_method_types=['alipay', 'wechat_pay']
            payment_method_options={
                    'wechat_pay': {
                    'client': 'web'
                    },
                }

        checkout_session = stripe.checkout.Session.create(
            payment_method_types = payment_method_types,
            payment_method_options =  payment_method_options,

            line_items=[
                {
                    'price': price,
                    'quantity': 1,
                },
            ],
            metadata = {'owner' : self.request.user},
            mode="payment",
            success_url='http://localhost:8000/payment-successful?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:8000/payment-canceled/',
        )
        return redirect(checkout_session.url)
    


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """
    Stripe webhook view to handle checkout session completed event.
    """

    def post(self, request, format=None):
        payload = request.body
        endpoint_secret = STRIPE_WEBHOOK_SECRET
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        event = None

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            print("Payment successful")

            payload_decoded = payload.decode().replace("'", '"')
            data = json.loads(payload_decoded)
            print(json.dumps(data, sort_keys=True, indent=2))

            amount = Decimal(data['data']['object']['amount_total'] / 100)
            currency = data['data']['object']['currency'].upper()
            user_name = data['data']['object']['metadata']['owner']
            user = User.objects.get(username=user_name)

            PurchaseHistory.objects.create(
                amount = amount,
                owner = user,
                currency = currency
            )

            # Add amount purchased to user's acct
            user.balance += amount
            user.save()

        return HttpResponse(status=200)
    

class SuccessfulPaymentView(View):

    def get(self, request):
        session = stripe.checkout.Session.retrieve(request.GET.get('session_id'))
        # amount = stripe.checkout.Session.retrieve(request.GET.get('amount_ total'))
        first_name = self.request.user.first_name
        # quantity = session['metadata']['quantity']
        amount = f"{(session['amount_total'] / 100):.2f}"
        currency = session['currency'].upper()
        symbol = '$' if currency == 'USD' else '¥'

        return render(request, 'members/stripe/success.html', 
                      {'customer' : first_name, 
                       'amount': amount, 
                       'currency': currency,
                       'symbol': symbol})