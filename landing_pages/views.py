from django.shortcuts import render
import datetime
from django.views import View

# Handles issue of importing from another folder/app
# import sys
# sys.path.append('.')
from members.pricing import *

class LandingPageView(View):

    template_name='landing_pages/ielts-multi-1.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context=self.get_context_data())
   
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
     
        print(kwargs)
        print('This fired!')
        return kwargs