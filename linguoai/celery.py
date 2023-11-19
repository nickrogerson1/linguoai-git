import os
from celery import Celery
import redis
import requests
from celery.schedules import crontab
import time

import environ

env = environ.Env()
environ.Env.read_env()

r = redis.Redis(host=env('REDISHOST'), port=env('REDISPORT'),username="default", password=env('REDISPASSWORD'),decode_responses=True)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "linguoai.settings")
app = Celery('linguoai',
             backend=env('REDIS_URL'),
             broker=env('REDIS_URL'))
app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.update(
    result_extended = True,
    worker_max_memory_per_child = 12000,
    worker_max_tasks_per_child = 2,
    worker_concurrency = 8
)

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')






@app.task
def check_exchange_rate(retry_no=0, delay=60):
    try:
        url = 'http://api.exchangerate.host/convert?access_key=68a479f003c5c91e2a034f7ee5a12b2a&from=CNY&to=USD&amount=1'
        res = requests.get(url).json()['info']['quote']
        print(res)
        r.set('cny_usd_rate', res)

    except Exception as e:
        print(e)
    # Wait a minute if less than 10 retries
        if retry_no < 10:
            retry_no += 1
            time.sleep(delay)
            return check_exchange_rate(retry_no)
        else:
        # Set the value at an arbitrary number
            r.set('cny_usd_rate', 13)
    



# Celery Beat config
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute='0', hour=[0,12]), check_exchange_rate.s(), name='Get Exchange Rate')