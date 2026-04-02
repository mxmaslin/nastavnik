import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from lessons.models import InteractionRecord

logger = logging.getLogger(__name__)


class LessonConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'lesson_{self.session_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected for session {self.session_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for session {self.session_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def interaction_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'interaction_update',
            'interaction_id': event['interaction_id'],
            'is_correct': event['is_correct'],
            'ml_service_success': event['ml_service_success']
        }))

    async def question_timeout(self, event):
        await self.send(text_data=json.dumps({
            'type': 'question_timeout',
            'question_id': event['question_id']
        }))

    @database_sync_to_async
    def get_interaction(self, interaction_id):
        try:
            return InteractionRecord.objects.get(id=interaction_id)
        except InteractionRecord.DoesNotExist:
            return None
