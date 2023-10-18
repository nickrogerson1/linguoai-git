from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F

from django.views import View
from ..models import PurchaseHistory, User, DiscountCodes

from decimal import Decimal
from datetime import date
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

        # Check if he's using a discount code
        discount_code_used = request.user.discount_code_used
        discount_code = request.user.discount_code

        bonus = percentage = ''

        if discount_code and not discount_code_used:
            expired = discount_code.expiry_date < date.today()
            if discount_code.for_purchases and not expired:
                if discount_code.bonus_amount:
                    bonus = discount_code.bonus_amount
                else:
                    bonus = discount_code.bonus_percent
                    percentage = True


        checkout_session = stripe.checkout.Session.create(
            payment_method_types = payment_method_types,
            payment_method_options =  payment_method_options,

            line_items=[
                {
                    'price': price,
                    'quantity': 1,
                },
            ],
            metadata = {'owner' : self.request.user,
                        'bonus' : bonus,
                        'percentage' : percentage
                    },
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
        

            discount_code_used = user.discount_code_used
            discount_code = user.discount_code

            if user.affiliate:
                user.affiliate.total_sales += amount
                user.affiliate.save()


            if discount_code and not discount_code_used:
                
                expired = discount_code.expiry_date < date.today()

                if discount_code.for_purchases and not expired:
                # Only apply it if it's not for sign ups and it's current
                    bonus_amount = discount_code.bonus_amount
                    
                    if bonus_amount:
                        user.balance = F('balance') + amount + bonus_amount
                    else:
                    # Need to work out the bonus percent
                        bonus_amount = amount * (discount_code.bonus_percent / 100)
                        user.balance = F('balance') + amount + bonus_amount
                    
                    discount_code.total_cost = F('total_cost') + bonus_amount
                    discount_code.times_used = F('times_used') + 1

                # If it's only for first purchases then chalk it off
                    if discount_code.first_purchase:
                        user.discount_code_used = True

                    discount_code.save()

                else:
                    user.balance = F('balance') + amount
            else:
                user.balance = F('balance') + amount
                
            user.save()

        return HttpResponse(status=200)
   
   

class SuccessfulPaymentView(View):

    def get(self, request):
        TWO_PLACES = Decimal("0.01")
        NO_PLACES = Decimal("1")

        session = stripe.checkout.Session.retrieve(request.GET.get('session_id'))
        user = self.request.user
        first_name = user.first_name
        amount = Decimal(session['amount_total'] / 100).quantize(TWO_PLACES)
        currency = session['currency'].upper()
        symbol = '$' if currency == 'USD' else '¥'

        bonus = Decimal(session['metadata']['bonus']).quantize(TWO_PLACES) if session['metadata']['bonus'] else 0
        percentage = session['metadata']['percentage']
        bonus_percent = ''

        if percentage:
            bonus_percent = bonus.quantize(NO_PLACES)
            bonus = (amount * (bonus / 100)).quantize(TWO_PLACES)

        total_amount = bonus + amount


        return render(request, 'members/stripe/success.html', 
                      {'customer' : first_name, 
                       'amount': amount, 
                       'currency': currency,
                       'symbol': symbol,
                       'bonus' : bonus,
                       'percentage' : percentage,
                       'bonus_percent' : bonus_percent,
                       'total_amount' : total_amount
                    })