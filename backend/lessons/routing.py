from django.urls import re_path
from lessons import consumers

websocket_urlpatterns = [
    re_path(r'ws/lesson/(?P<session_id>\w+)/$', consumers.LessonConsumer.as_asgi()),
]
