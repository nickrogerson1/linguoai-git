from decimal import Decimal as D

from .api_funcs.ielts_score import *
from .api_funcs.corrections import get_corrected_submission
from .api_funcs.improved import get_improved_submission

from .models import *

import time
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from linguoai.celery import app, check_exchange_rate
from celery.utils.time import get_exponential_backoff_interval

import re
import redis
import tiktoken

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import environ
env = environ.Env()
environ.Env.read_env()

r = redis.Redis(host=env('REDISHOST'), port=env('REDISPORT'),username="default", password=env('REDISPASSWORD'),decode_responses=True)


from .pricing import *

from django.db import transaction



# This is the max retries for all the functions set in one place. 
# This also sets it for the JS.
MAX_RETRIES = 10


# TEST THIS FUNCTION!!
# Get exchange from API
def get_exchange_rate():
    cny_usd_rate = r.get('cny_usd_rate')
    print(f'Rate: {cny_usd_rate}')
    if cny_usd_rate:
# bytes are returned, so needs converting
        return float(cny_usd_rate)
    else:
# if there's no value (unlikely), call it and do it again
# Retry it less and speed up the requests as a client will be waiting
        val = check_exchange_rate(retry_no=5,delay=5)
        if val:
            return val
    # Return an arbitrary figure (as of 2023)
        return 13







                                                                
def update_db(model, data, start_time, user_id, task_id, price, total_words, charged, 
sub=None, question=None, answer=None, score_res=None, band=None, lang=None):

# data = [result, model, prompt_tokens, completion_tokens, total_tokens] 

# IELTS Writing task 2 update
    if answer:
        model.question = question
        model.answer = answer
        model.score_res = score_res
        model.band = band
        model.explanation_language = lang
        sub_type = 'Ielts Writing Task 2'


# The rest
    if sub:
        model.submission = sub.replace('\n', '<br>')

        # Add all the openai data to the db
        # [html, model_used, prompt_tokens, completion_tokens, total_tokens]
        result = data[0].replace('\n', '<br>').lstrip()

        if isinstance(model, CorrectedSubmission):
            model.result = result
            sub_type = 'Corrected Submission'

        if isinstance(model, ImprovedSubmission):
            model.improved_sub = result
            sub_type = 'Improved Submission'


    if data[1].startswith('gpt-3'):
        model_used = 'gpt-3'
    elif data[1].endswith('-preview'):
        model_used = 'gpt-4-turbo'
    else:
        model_used = 'gpt-4'
   

    model.model_used = model_used
    model.prompt_tokens = data[2]
    model.completion_tokens = data[3]
    model.total_tokens = data[4]
    

    # Work out cost for me
    cost = round(D(data[2] / 1000) * D(LLM_COSTS[model_used]['input']) + D(data[3] / 1000) * D(LLM_COSTS[model_used]['output']), 4)

    

# Save charged before continuing to make USD calculations
    model.charged = charged

# Deduct the amount from their balance and add total submission
# Do this here before converted into dollars

# NEED A LOCK HERE!
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        user.balance -= D(charged)
        user.total_spent += D(charged)
        user.total_submissions += 1
        user.save()

     # Add them to the current db
    model.owner = user

    model.new_balance = user.balance

# Get the charges into dollars to make USD calculations
    usd_exchange_rate = 1

    if user.currency == 'CNY':
        usd_exchange_rate = get_exchange_rate()
        charged = charged * D(usd_exchange_rate)
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

    print(f'USERNAME: {user.username}')
    print(f'PRICE per 100 words: {price}')
    print(f'PROCESSING TIME: {model.processing_time}')

    # time.sleep(5)
    model.save()

    pk = model.pk
    
    time_created = time.mktime(model.time_created.timetuple()) * 1000

# Inform websocket
    channel_name = r.hget(user.username, 'channel')
# Check that there's a name
    if channel_name:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(channel_name, {
            'type': 'update',
            'status': 'success',
            'taskId' : f'r-{task_id}',
            'newBalance' : float(user.balance),
            'pk' : pk,
            'timeCreated' : time_created,
            'subType' : sub_type
        })
    
    return [pk, user.balance, time_created]
    


def update_before_retry(retries, this_delay, task_id, username):
    
# Inform websocket
    channel_name = r.hget(username, 'channel')
# Check that there's a name
    if channel_name:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(channel_name, {
            'type': 'update',
            'status': 'failed',
            'maxRetries' : MAX_RETRIES,
    # Adding 1 as it has failed and is attempting its retry next
            'retryCount' : retries,
            'delay' : this_delay,
            'taskId' : f'r-{task_id}'
        })


# Remove the worker after 40 secs in case HTTP request super slow
@shared_task
def remove_expired_task_ids(username, store_val):
    r.lrem(f'{username}_pending', 1, store_val)
    print('LRANGE 2: ' + str(r.lrange(f'{username}_pending',0,-1)))







@shared_task(bind=True)
def get_results(self, req_type, t0, username, user_id, sub, from_where, price_per_100_words, total_words, charged, file_name, curr):

    task_id = self.request.id
    print(f'TASK ID {task_id}')

    # Only send on the first run for multi
    if from_where == 'multi' and not self.request.retries:
        # Inform websocket
        channel_name = r.hget(username, 'channel')
        # Check that there's a name
        if channel_name:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(channel_name, {
                'type': 'update',
                'wordCount': total_words,
                'cost': f'{curr}{charged}',
                'fileName': file_name,
                'taskId' : f'r-{task_id}',
                'status': 'Awaiting Response',
            })
    
    store_val = f'{req_type.capitalize()} Submission,' + task_id
    task_pending = r.lpos(f'{username}_pending', store_val)
    print(f'LPOS: {task_pending}')

# None is returned when doesn't exist. 0 is for pos zero
    if task_pending == None:
        # Add to all the pending tasks for this user
        r.lpush(f'{username}_pending', store_val)
        print('LRANGE 1: ' + str(r.lrange(f'{username}_pending',0,-1)))

    # Replace old single value with new one (if there is one)
    # and delete it after 2 minutes
    if from_where == 'single':
        r.set(f'{username}_single', task_id, ex=120)

    enc = tiktoken.encoding_for_model('gpt-4')
    num_tokens = len(enc.encode(sub))

    print(f'Tokens Used: {num_tokens}')
    print(f'Word Count: {total_words}')

# Check to see whether API limit has been hit and can make a request
    t0 = time.time()
    # check_and_reduce_usage_left(num_tokens, task_id)
    print(f'SUB: {sub}')

    try:
        # Long API call
        if req_type == 'corrected':
            data = get_corrected_submission(sub)
        else:
            data = get_improved_submission(sub)
    
    except Exception as e:
        retries = self.request.retries
        print(f'RETRY NO: {retries}')
        print(e)

        try:
            if retries == MAX_RETRIES:
                raise MaxRetriesExceededError
            
            # Using utility function for exponential backoff as need to process Exceptions
            # This is not possible with decorators or custom classes
            # factor, retries, max, full jitter 
            this_delay = get_exponential_backoff_interval(10,retries,300,True)
            update_before_retry(retries, this_delay, task_id, username)
            # Otherwise retry again
            raise self.retry(exc=e, countdown=this_delay, max_retries=MAX_RETRIES)

        except MaxRetriesExceededError:
        # Inform websocket
            channel_name = r.hget(username, 'channel')
        # Check that there's a name
            if channel_name:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(channel_name, {
                    'type': 'update',
                    'status': 'failed',
                    'retryCount' : retries,
                    'taskId' : f'r-{task_id}'
                })

            remove_expired_task_ids.apply_async((username, store_val), countdown=40)
            return print('MAX RETRIES EXCEEDED!')
        
    # Create an instance to pass to next func
    model = CorrectedSubmission() if req_type == 'corrected' else ImprovedSubmission()

    if data:
        extra = update_db(model, data, t0, user_id, task_id, price_per_100_words, total_words, charged, sub=sub)

    # Save PK and balance in case it beats HTTP
    # Unnecessary for multi
        self.request.kwargs = {
            'pk' : extra[0],
            'new_balance' : extra[1],
            'time_created' : extra[2],
            'sub_type' : req_type
        }

    # Remove completed item from list
    remove_expired_task_ids.apply_async((username, store_val), countdown=40)







@shared_task(bind=True)
def get_ielts_writing_task_2_scores(self, t0, username, user_id, q, a, lang, lang_code, price_per_100_words, total_words, charged, lang_model=None):

    task_id = self.request.id
    print(f'TASK ID {task_id}')

    store_val = 'Ielts Writing Task 2,' + task_id
    print(store_val)

    task_pending = r.lpos(f'{username}_pending', store_val)
    print(f'LPOS: {task_pending}')

# None is returned when doesn't exist. 0 is for pos zero
    if task_pending == None:
        # Add to all the pending tasks for this user
        r.lpush(f'{username}_pending', store_val)
        print('LRANGE 1: ' + str(r.lrange(f'{username}_pending',0,-1)))

    # Replace old single value with new one (if there is one)
    # and delete it after 2 minutes
    r.set(f'{username}_single', task_id, ex=120)

    enc = tiktoken.encoding_for_model('gpt-4')
    q_toks = len(enc.encode(q))
    a_toks = len(enc.encode(a))
    num_tokens = q_toks + a_toks

    print(f'Tokens Used: {num_tokens}')
    print(f'Word Count: {total_words}')


    try:
        # Long API call
        data = get_ielts_writing_task_2_score(q,a,lang, lang_model)
       
    except Exception as e:
        retries = self.request.retries
        
        try:
            if retries == MAX_RETRIES:
                raise MaxRetriesExceededError
           
            this_delay = get_exponential_backoff_interval(10,retries,300,True)
            # Otherwise retry again
            update_before_retry(retries, this_delay, task_id, username)
            raise self.retry(exc=e, countdown=this_delay, max_retries=MAX_RETRIES)

        except MaxRetriesExceededError:
        # Inform websocket
            channel_name = r.hget(username, 'channel')
        # Check that there's a name
            if channel_name:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(channel_name, {
                    'type': 'update',
                    'status': 'failed',
                    'retryCount' : retries,
                    'taskId' : f'r-{task_id}'
                })

            remove_expired_task_ids.apply_async((username, store_val), countdown=40)
            return print('MAX RETRIES EXCEEDED!')
        
    # Create an instance to pass to next func
    model = IeltsWritingTask2()

    if data:
        print(data[0])

    # Pull out the band and replace it with nothing
        reg = r'%%%%%([a-zA-Z0-9_\. ]+)%%%%%'
        m = re.search(reg, data[0], flags=re.I)

        band = m.group(1).replace('Band ', '')

        # Remove \n and change to <br>
        question = q.replace('\n', '<br>')
        answer = a.replace('\n', '<br>')
        # Get rid of first two breaks as well for admin interface
        score = re.sub(reg, '', data[0])
        # score_res = score.replace('\n', '<br>').replace('<br>','',2)
        score_res = score.replace('\n', '')

        extra = update_db(model, data, t0, user_id, task_id, price_per_100_words, total_words, charged, 
                question=question, answer=answer, score_res=score_res, band=band, lang=lang_code)

    # Save PK and balance in case it beats HTTP
    # Unnecessary for multi
        self.request.kwargs = {
            'pk' : extra[0],
            'new_balance' : extra[1],
            'time_created' : extra[2],
            'sub_type' : 'ielts-writing-task-2'
        }
    # Remove completed item from list
    remove_expired_task_ids.apply_async((username, store_val), countdown=40)