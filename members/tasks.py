from decimal import Decimal


from .api_funcs.ielts_score import *
from .api_funcs.corrections import call_and_find_difference
from .api_funcs.improved import improved_submission


from .models import *

import time
from celery import shared_task

import re




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
        'USD': 0.04,
        'CNY': 0.3
    },
    'improved_results': {
        'USD': 0.04,
        'CNY': 0.3
    }
}



                                                                
def update_db(model, data, start_time, user_id, price, total_words, charged, 
sub=None, question=None, answer=None, score_res=None, band=None, lang=None):


# IELTS Writing task 2 update
    if answer:
        model.question = question
        model.answer = answer
        model.score_res = score_res
        model.band = band
        model.explanation_language = lang


# The rest
    if sub:
        model.submission = sub.replace('\n', '<br>')

        # Add all the openai data to the db
        # [html, model_used, prompt_tokens, completion_tokens, total_tokens]
        result = data[0].replace('\n', '<br>').lstrip()

        if isinstance(model, CorrectedSubmission):
            model.result = result

        if isinstance(model, ImprovedSubmission):
            model.improved_sub = result

   

    model.model_used = data[1]
    model.prompt_tokens = data[2]
    model.completion_tokens = data[3]
    model.total_tokens = data[4]
    
    if data[1].startswith('gpt-3'):
        model_used = 'gpt-3'
    elif data[1].startswith('gpt-4'):
        model_used = 'gpt-4'

    # Work out cost for me
    cost = round((data[2] / 1000) * LLM_COSTS[model_used]['input'] + (data[3] / 1000) * LLM_COSTS[model_used]['output'], 4)

    user = User.objects.get(pk=user_id)

# Save charged before continuing to make USD calculations
    model.charged = charged

# Deduct the amount from their balance and add total submission
# Do this here before converted into dollars
    user.balance -= Decimal(charged)
    user.total_submissions += 1
    user.save()

     # Add them to the current db
    model.owner = user

    model.new_balance = user.balance

# Get the charges into dollars to make USD calculations
    usd_exchange_rate = 1

    if user.currency == 'CNY':
        usd_exchange_rate = 0.14
        charged = charged * usd_exchange_rate
    # Add this to the db to make it more coherent
        model.usd_charge = charged

    profit = charged - cost
    margin = round((profit / cost) * 100, 3)

    print(f'Exchange rate: {usd_exchange_rate}')

    # Then save them
    model.currency = user.currency
    model.cost = cost
    model.total_words = total_words
    model.price_per_100_words = price
    model.usd_exchange_rate = usd_exchange_rate
    model.profit = profit
    model.margin = margin

    # Record the time it took
    t1 = time.time()
    model.processing_time = round(t1 - start_time, 3)
    model.save()

    return 


    # Context only info
    # Let the template know this was a new search and not a lookup
    # model.new_search = True
    # model.symbol = '$' if user.currency == 'USD' else '¥'
    # model.balance = Decimal(u.balance).quantize(Decimal('0.01'))

    # model.pk = model.pk

    

@shared_task
def get_corrected_results(t0, user_id, sub, price_per_100_words, total_words, charged):

    # Long API call
    data = call_and_find_difference(sub)
    # Create an instance to pass to next func
    model = CorrectedSubmission()

    if data:
        return update_db(model, data, t0, user_id, price_per_100_words, total_words, charged, sub=sub)


@shared_task
def get_improved_results(t0, user_id, sub, price_per_100_words, total_words, charged):

    data = improved_submission(sub)
    # Create an instance to pass to next func
    model = ImprovedSubmission()

    if data:
        return update_db(model, data, t0, user_id, price_per_100_words, total_words, charged, sub=sub)




@shared_task
def get_ielts_writing_task_2_scores(t0, user_id, q, a, lang, lang_code, price_per_100_words, total_words, charged):
 
 # Add all the openai data to the db
# [html, model, prompt_tokens, completion_tokens, total_tokens]
    data = get_ielts_writing_task_2_score(q,a,lang)

    model = IeltsWritingTask2()

    if data:

        # Pull out the band and replace it with nothing
        reg = r'%%%%%([a-zA-Z0-9_\. ]+)%%%%%'
        m = re.search(reg, data[0], flags=re.I)
        band = m.group(1).replace('Band ', '')

        # Remove \n and change to <br>
        question = q.replace('\n', '<br>')
        answer = a.replace('\n', '<br>')
        # Get rid of first two breaks as well for admin interface
        score = re.sub(reg, '', data[0])
        score_res = score.replace('\n', '<br>').replace('<br>','',2)

        # get_context_data_post(data, t0, price_per_100_words, total_words, charged, q, a)

        return update_db(model, data, t0, user_id, price_per_100_words, total_words, charged, 
                question=question, answer=answer, score_res=score_res, band=band, lang=lang_code)








from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from .copies.pdf import get_pdf
from django.http import HttpResponse


@shared_task
def get_bulk_pdf(sub_type, user, pks, type=None):

    # origin = request.path.split('/')[1]
    if sub_type == 'corrected-results':
        filename = f'{user}-pdf-corrections.zip'
    elif sub_type == 'improved-results':
        filename = f'{user}-pdf-improved.zip'
    else:
        filename = f'{user}-pdf-ielts-writing-task-2.zip'
        

    # Ignore last one as it's empty
    pks = pks.split('/')[:-1]
    print(f'PKS: {pks}')

    # if just one file, return as is 
    if len(pks) == 1:
        return get_pdf(sub_type, user, pks[0], type)

    # Otherwise zip them
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pk in pks:
            fetch_file = get_pdf(sub_type, user, pk, type, multi=True)
            pdf = fetch_file[0]
            lf = fetch_file[1]
            b = BytesIO(pdf)
            f.writestr(lf, b.getvalue())

    # headers = {
    #     'Content-Disposition': f'attachment; filename="{filename}"',
    #     'Content-Type': 'application/zip'
    # }
        
    # return HttpResponse(buffer.getvalue(), headers=headers)

    # Save to S3 bucket for 24 hours & maybe update db or email it them
    # print('Saved to S3 bucket!')
    
  

    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #         user, {"type": "send.message", 'message': 'data'}
        # )




@shared_task
def get_bulk_mixed_pdf(request, url_str):

    filename = f'{request.user}-pdfs.zip'
    url_list = url_str.split("/")[:-1]

    # # Split them into chunks
    pairs = [url_list[i:i+2] for i in range(0, len(url_list),2)]
    print(f'Pairs: {pairs}')

    # # if just one file, return as is 
    if len(pairs) == 1:
        return get_pdf(request, pairs[0][1], sub=pairs[0][0])

    # # Otherwise zip them
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_DEFLATED) as f:
        for pair in pairs:
            fetch_file = get_pdf(request, pair[1], type=True, multi=True, sub=pair[0])
            pdf = fetch_file[0]
            fn = fetch_file[1]
            b = BytesIO(pdf)
            f.writestr(fn, b.getvalue())

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'application/zip'
    }
        
    return HttpResponse(buffer.getvalue(), headers=headers)