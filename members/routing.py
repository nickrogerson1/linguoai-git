from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/bulk-submission/", consumers.Consumer.as_asgi()),
    re_path(r"ws/single-submission/", consumers.SingleConsumer.as_asgi()),
    re_path(r"ws/log-submission/", consumers.LogConsumer.as_asgi()),
]