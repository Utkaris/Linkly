from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django.contrib.auth.models import AnonymousUser

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
)

from .serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for chat conversations.
    """

    async def connect(self):

        self.user = self.scope["user"]

        if (
            isinstance(self.user, AnonymousUser)
            or not self.user.is_authenticated
        ):
            await self.close(code=4001)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"][
            "conversation_id"
        ]

        is_allowed = await self.is_participant()

        if not is_allowed:
            await self.close(code=4003)
            return

        self.room_group_name = (
            f"chat_{self.conversation_id}"
        )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send_json(
            {
                "type": "connection",
                "success": True,
                "message": "Connected successfully.",
            }
        )

    async def disconnect(self, close_code):

        if hasattr(self, "room_group_name"):

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        """
        Handle websocket events.
        """

        event_type = content.get("type")

        if event_type == "ping":

            await self.send_json(
                {
                    "type": "pong",
                }
            )

            return

        if event_type == "message":

            message = await self.save_message(content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                },
            )

            return

        await self.send_json(
            {
                "type": "error",
                "message": "Unsupported event type.",
            }
        )

    async def chat_message(self, event):
        """
        Broadcast saved message to all participants.
        """

        await self.send_json(
            {
                "type": "message",
                "data": event["message"],
            }
        )

    @database_sync_to_async
    def is_participant(self):

        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
            is_removed=False,
        ).exists()

    @database_sync_to_async
    def save_message(self, data):
        """
        Save a websocket message to the database.
        """

        conversation = Conversation.objects.get(
            id=self.conversation_id,
        )

        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=data.get("content", ""),
            message_type=data.get(
                "message_type",
                "text",
            ),
        )

        return MessageSerializer(message).data