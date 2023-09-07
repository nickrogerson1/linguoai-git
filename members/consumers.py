import json

from channels.generic.websocket import WebsocketConsumer
from channels.consumer import AsyncConsumer
import redis
import json
from django.db.models import Value

import environ
env = environ.Env()
environ.Env.read_env()

r = redis.Redis(host=env('REDISHOST'), port=env('REDISPORT'),username="default", password=env('REDISPASSWORD'))

class Consumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        print(self.scope['user'].username)
        
    # Cache the username and channel
        r.hset(self.scope['user'].username, mapping={'channel' : self.channel_name})
        print(f'CHANNEL NAME: {self.channel_name}')
        self.send(json.dumps({'message':"Connected"}))
        

    def disconnect(self, close_code):
        #  r = redis.Redis()
    # Remove the user from Redis
         r.delete(self.scope['user'].username)
         print(self.scope['user'].username)
         self.close()

    # def receive(self, text_data=None, bytes_data=None):
    #     print(f'WS received: {text_data}')

    
    def update(self, vals):
        self.send(json.dumps(vals))
        



from linguoai.celery import app
from celery.result import AsyncResult

class SingleConsumer(Consumer):
    # Has to check that the HTTP request wasn't beaten by the Celery worker
    # On connect, query Redis to get worker ID and then check the status AsyncResult(self.request.id).ready()
    # If the worker has finished, then update results
    # If not, then wait

    def connect(self):
        self.accept()

        username = self.scope['user'].username
        print(f'USERNAME {username}')
        task_id = r.hget(username, 'single_sub')

        if task_id:
            task_id = task_id.decode()

        print(f'TASK ID {task_id}')

        status = AsyncResult(task_id).ready()
        print(f'Status: {status}')

    # if it's somehow already finished, then get the result
        print(f'ASYNC KWARGS: {AsyncResult(task_id).kwargs}')
        # Get the PK to make the new url link
        pk = AsyncResult(task_id).kwargs['pk'] if status else ''
    # Send it back as Float as Decimals are not serializable
        new_balance = float(AsyncResult(task_id).kwargs['new_balance']) if status else ''
        
    # Cache the username and channel
        print(self.scope['user'].username)
        r.hset(self.scope['user'].username, mapping={'channel' : self.channel_name})
        
        print(f'CHANNEL NAME: {self.channel_name}')
        self.send(json.dumps({'ready': status, 'pk' : pk, 'new_balance' : new_balance}))
