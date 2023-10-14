from decimal import Decimal as D

from .api_funcs.ielts_score import *
from .api_funcs.corrections import get_corrected_submission
from .api_funcs.improved import get_improved_submission

from .models import *

import time
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from linguoai.celery import app
from celery.utils.time import get_exponential_backoff_interval

import requests

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

# This is the max retries for all the functions set in one place
MAX_RETRIES = 6


# Update exchange rate every hour
# celery beat worker updates Redis cache every hour
# exchange rate is called when currency is CNY
# if no exchange rate present (ie due to data loss) then call API itself and cache its value

# from linguoai.celery import check_exchange_rate

# OPTIONS
# imf
# rba - Reserve Bank of Australia
# boc - Bank of Canada
# snb - Swiss National Bank
# cbr - Central Bank of Russia
# nbu - National Bank of Ukraine
# bnro - National Bank of Romania
# boi - Bank of Israel
# nob - Norges Bank (Norway monetary policy)
# cbn - Central Bank of Nigeria
# ecb

def check_exchange_rate():
    url = 'https://api.exchangerate.host/latest?base=cny&source=rba'
    # data = {'source':'imf', 'base':'cny', 'symbols':'usd, gbp'}
    res = requests.get(url).json()['rates']['USD']
    # ['info']['rate']
    print(res)
    # r.set('cny_usd_rate', res)




# Get exchange from API
def get_exchange_rate():
    cny_usd_rate = r.get('cny_usd_rate')
    print(f'Rate: {cny_usd_rate}')
    if cny_usd_rate:
# bytes are returned, so needs converting
        return float(cny_usd_rate)
    else:
# if there's no value (unlikely), call it and do it again
        check_exchange_rate()
        get_exchange_rate()





                                                                
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

   

    model.model_used = data[1]
    model.prompt_tokens = data[2]
    model.completion_tokens = data[3]
    model.total_tokens = data[4]
    
    if data[1].startswith('gpt-3'):
        model_used = 'gpt-3'
    elif data[1].startswith('gpt-4'):
        model_used = 'gpt-4'

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
        user.total_submissions += 1
        user.save()

     # Add them to the current db
    model.owner = user

    model.new_balance = user.balance

# Get the charges into dollars to make USD calculations
    usd_exchange_rate = 1

    if user.currency == 'CNY':
        usd_exchange_rate = get_exchange_rate()
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
    
   




# 40k tokens and 200 requests per min
@shared_task
def update_tokens_left(num_tokens):
    with r.lock('update_openai'):
        tokens_left, requests_left = r.hmget('openai_remain_usage',['tokens','requests'])
        # Re-add tokens and a req after 1 minute
        tokens_left_now = int(tokens_left) + num_tokens
        # Always one request
        requests_left = int(requests_left) + 1
        # Save new values to Redis
        r.hset('openai_remain_usage', mapping={'tokens' : tokens_left_now, 'requests' : requests_left})



def check_and_reduce_usage_left(num_tokens, task_id):
     
    lock = r.lock('update_openai')
    lock.acquire()
    tokens_left, requests_left = (r.hmget('openai_remain_usage',['tokens','requests'])
                if r.exists('openai_remain_usage') else [40000,200])

# If there are enough tokens and requests left, then process it
    if tokens_left > 0 and requests_left > 0:
        tokens_left_now = int(tokens_left) - num_tokens
        requests_left = int(requests_left) - 1
        # Save new value to Redis
        r.hset('openai_remain_usage', mapping={'tokens' : tokens_left_now, 'requests' : requests_left})
        lock.release()
        update_tokens_left_worker = update_tokens_left.apply_async((num_tokens,), countdown=60)
        return r.hset('update_tokens_left_worker', mapping={task_id: update_tokens_left_worker.id})
    else:
# Otherwise wait for more availability
        lock.release()
        time.sleep(2)
        return check_and_reduce_usage_left(num_tokens)




def update_before_retry(retries, max_retries, this_delay, task_id, username, num_tokens, t0):
    
# Check here whether browser has requested to stop reporting this task
    if retries < max_retries:
    # Inform websocket
        channel_name = r.hget(username, 'channel')
    # Check that there's a name
        if channel_name:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(channel_name, {
                'type': 'update',
                'status': 'failed',
                'subType' : 'corrections',
        # Adding 1 as it has failed and is attempting its retry next
                'retryCount' : retries,
                'delay' : this_delay,
                'taskId' : f'r-{task_id}'
            })
    
    # Update openai request as worker failed and didnt reduce usage amount
    runtime = time.time() - t0
    print(f'CURRENT RUNTIME: {runtime}')
    if runtime < 60:
        worker_to_kill_id = r.hget('update_tokens_left_worker', task_id)
        # print(f'WORKER TO KILL ID: {worker_to_kill_id}')
        app.control.revoke(worker_to_kill_id, terminate=True)

        r.hdel('update_tokens_left_worker', task_id)
        # print(f"TASK ID NOW: {r.hget('update_tokens_left_worker', task_id)}")
        update_tokens_left(num_tokens)


# Remove the worker after 40 secs in case HTTP request super slow
@shared_task
def remove_expired_task_ids(username, store_val):
    r.lrem(f'{username}_pending', 1, store_val)
    print('LRANGE 2: ' + str(r.lrange(f'{username}_pending',0,-1)))







@shared_task(bind=True)
def get_corrected_results(self, t0, username, user_id, sub, from_where, price_per_100_words, total_words, charged, file_name, curr):

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

    store_val = 'Corrected Submission,' + task_id
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
    check_and_reduce_usage_left(num_tokens, task_id)

    try:
        # Long API call
        data = get_corrected_submission(sub)
        # print(f'Sleeping for 1 second')
        # time.sleep(10)
        # data = [result, model, prompt_tokens, completion_tokens, total_tokens] 
        # data = ['Some Corrected result', 'gpt-4', 100, 100, 200]
        # time.sleep(7)
    except Exception as e:
        retries = self.request.retries

        # Using utility function for exponential backoff as need to process Exceptions
        # This is not possible with decorators or custom classes
        # factor, retries, max, full jitter 
        this_delay = get_exponential_backoff_interval(1,retries,300,True)
        print(f'RETRY NO: {retries}')
        update_before_retry(retries, MAX_RETRIES, this_delay, task_id, username, num_tokens, t0)
   
        try:
            if retries == MAX_RETRIES:
                raise MaxRetriesExceededError
            # Simulate delay before retrying
            # time.sleep(3)
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
    model = CorrectedSubmission()

    if data:
        extra = update_db(model, data, t0, user_id, task_id, price_per_100_words, total_words, charged, sub=sub)

    # Save PK and balance in case it beats HTTP
    # Unnecessary for multi
        self.request.kwargs = {
            'pk' : extra[0],
            'new_balance' : extra[1],
            'time_created' : extra[2],
            'sub_type' : 'corrected'
        }
    # Remove completed item from list
    remove_expired_task_ids.apply_async((username, store_val), countdown=40)

       






@shared_task(bind=True)
def get_improved_results(self, t0, username, user_id, sub, from_where, price_per_100_words, total_words, charged, file_name, curr):

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

    store_val = 'Improved Submission,' + task_id
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
    check_and_reduce_usage_left(num_tokens, task_id)

    try:
        # Long API call
        data = get_improved_submission(sub)
        # print(f'Sleeping for 1 second')
        # time.sleep(10)
        # data = [result, model, prompt_tokens, completion_tokens, total_tokens] 
        # data = ['Some Corrected result', 'gpt-4', 100, 100, 200]
        # time.sleep(7)
    except Exception as e:
        retries = self.request.retries
        # Using utility function for exponential backoff as need to process Exceptions
        # This is not possible with decorators or custom classes
        # factor, retries, max, full jitter 
        this_delay = get_exponential_backoff_interval(1,retries,300,True)

        update_before_retry(retries, MAX_RETRIES, this_delay, task_id, username, num_tokens, t0)
   
        try:
            if retries == MAX_RETRIES:
                raise MaxRetriesExceededError
            # Simulate delay before retrying
            # time.sleep(3)
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
    model = ImprovedSubmission()

    if data:
        extra = update_db(model, data, t0, user_id, task_id, price_per_100_words, total_words, charged, sub=sub)

    # Save PK and balance in case it beats HTTP
    # Unnecessary for multi
        self.request.kwargs = {
            'pk' : extra[0],
            'new_balance' : extra[1],
            'time_created' : extra[2],
            'sub_type' : 'improved'
        }
    # Remove completed item from list
    remove_expired_task_ids.apply_async((username, store_val), countdown=40)











@shared_task(bind=True)
def get_ielts_writing_task_2_scores(self, t0, username, user_id, q, a, lang, lang_code, price_per_100_words, total_words, charged):

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

# Check to see whether API limit has been hit and can make a request
    t0 = time.time()
    check_and_reduce_usage_left(num_tokens, task_id)

    try:
        # Long API call
        data = get_ielts_writing_task_2_score(q,a,lang)
        # print(f'Sleeping for 1 second')
        # time.sleep(3)
        # [html, model, prompt_tokens, completion_tokens, total_tokens]
        # data = ['Some Ielts Writing result', 'gpt-4', 100, 100, 200]
    except Exception as e:
        retries = self.request.retries
        # Using utility function for exponential backoff as need to process Exceptions
        # This is not possible with decorators or custom classes
        # factor, retries, max, full jitter 
        this_delay = get_exponential_backoff_interval(1,retries,300,True)

        update_before_retry(retries, MAX_RETRIES, this_delay, task_id, username, num_tokens, t0)
   
        try:
            if retries == MAX_RETRIES:
                raise MaxRetriesExceededError
            # Simulate delay before retrying
            # time.sleep(3)
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
    model = IeltsWritingTask2()

    if data:
    # Pull out the band and replace it with nothing
        reg = r'%%%%%([a-zA-Z0-9_\. ]+)%%%%%'
        m = re.search(reg, data[0], flags=re.I)

    # CHANGE BACK FOR PRODUCTION!!!!
        # band = m.group(1).replace('Band ', '')
        band = 6

        # Remove \n and change to <br>
        question = q.replace('\n', '<br>')
        answer = a.replace('\n', '<br>')
        # Get rid of first two breaks as well for admin interface
        score = re.sub(reg, '', data[0])
        score_res = score.replace('\n', '<br>').replace('<br>','',2)

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