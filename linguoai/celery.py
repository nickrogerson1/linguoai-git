import os
from celery import Celery
import redis
import requests
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "linguoai.settings")
app = Celery("linguoai")
app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.update(
    result_extended = True
)

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')




# Celery Beat config
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass
    # sender.add_periodic_task(crontab(minute='0', hour='*'), check_exchange_rate.s(), name='Get Exchange Rate')
    # sender.add_periodic_task(5.0, send_to_ws.s(), name='Send to WS')





# @app.task
# def check_exchange_rate():
#     url = 'https://api.exchangerate.host/convert?from=CNY&to=USD'
#     res = requests.get(url).json()['info']['rate']
#     print(res)
#     r = redis.Redis()
#     r.set('cny_usd_rate', res)



# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

# @app.task
# def send_to_ws():
#     r = redis.Redis()
#     channel_name = r.get('admin').decode()
#     if channel_name:
#         channel_layer = get_channel_layer()
#         print(channel_layer.group_channels('Nicks cool group'))
        
#         return async_to_sync(channel_layer.send)(channel_name, {
#             'type': 'status.update',
#             'text': 'success'
#         })
#     return 'Nothing to send.'