from channels.generic.websocket import WebsocketConsumer
import redis
import json
from celery.result import AsyncResult

import environ
env = environ.Env()
environ.Env.read_env()

r = redis.Redis(host=env('REDISHOST'), port=env('REDISPORT'),username="default", password=env('REDISPASSWORD'),decode_responses=True)

class Consumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        r.delete(self.scope['user'].username)
        username = self.scope['user'].username
        print(f"CONSUMER USERNAME: {username}")
        
    # Cache the username and channel
        r.hset(self.scope['user'].username, mapping={'channel' : self.channel_name})
        print(f'CHANNEL NAME: {self.channel_name}')
        self.send(json.dumps({'message':"Connected"}))
        

    def disconnect(self, close_code):
    # Remove the user from Redis - clears the id
         r.delete(self.scope['user'].username)
         print(f"CONSUMER USERNAME DISCONNECT: {self.scope['user'].username}")
         self.close()

    
    def update(self, vals):
        self.send(json.dumps(vals))
        





class SingleConsumer(Consumer):
    # Has to check that the HTTP request wasn't beaten by the Celery worker
    # On connect, query Redis to get worker ID and then check the status AsyncResult(self.request.id).ready()
    # If the worker has finished, then update results
    # If not, then wait

    def connect(self):
        self.accept()

        username = self.scope['user'].username
        print(f'CONNECT USERNAME: {username}')
        task_id = r.get(f'{username}_single')
        print(f'TASK ID SINGLE CONSUMER: {task_id}')

        status = AsyncResult(task_id).ready()
        print(f'Status: {status}')

    # If it's somehow already finished, then get the result
        print(f'ASYNC KWARGS: {AsyncResult(task_id).kwargs}')
    # Get the PK to make the new url link
        pk = AsyncResult(task_id).kwargs['pk'] if status else ''
    # Send it back as Float as Decimals are not serializable
        new_balance = float(AsyncResult(task_id).kwargs['new_balance']) if status else ''
        
    # Cache the username and channel
        print(f"CONSUMER USERNAME CACHING: {username}")
        r.hset(username, mapping={'channel' : self.channel_name})
        
        print(f'CHANNEL NAME: {self.channel_name}')
        self.send(json.dumps({'ready': status, 'pk' : pk, 'new_balance' : new_balance}))





# Look for the last result matching the sub_type and then add in the link and change to completed and time_created

class LogConsumer(Consumer):

    def connect(self):
        self.accept()

        username = self.scope['user'].username
        print(f'CONNECT USERNAME: {username}')

        pending_items = r.lrange(f'{username}_pending', 0, -1)
        print(f'PENDING ITEMS: {pending_items}')

        if pending_items:
        # Check their status
            print('MADE IT HERE!')

            for item in pending_items:
                print(f'CONSUMER TASK ID: {item}')
            
                sub_type, task_id = item.split(',')
                # sub_type = sub_type.split(' ')[0].lower()

                status = AsyncResult(task_id).ready()
                print(f'Status: {status}')

            # If it's somehow already finished, then get the result
                print(f'ASYNC KWARGS: {AsyncResult(task_id).kwargs}')
            # Get the PK to make the new url link
                pk = AsyncResult(task_id).kwargs['pk'] if status else ''
            # Send it back as Float as Decimals are not serializable
                new_balance = float(AsyncResult(task_id).kwargs['new_balance']) if status else ''
                time_created = AsyncResult(task_id).kwargs['time_created'] if status else ''

                self.send(json.dumps({
                    'ready': status, 
                    'pk' : pk, 
                    'new_balance' : new_balance,
                    'time_created' : time_created,
                    'sub_type' : sub_type
                }))
        
        # Cache the username and channel
        print(f"CONSUMER USERNAME CACHING: {username}")
        print(f'CHANNEL NAME: {self.channel_name}')
        r.hset(self.scope['user'].username, mapping={'channel' : self.channel_name})
        
        
