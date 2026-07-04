from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReaction,
)

from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    CreateConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
    EditMessageSerializer,
    MessageReactionSerializer,
    ReadReceiptSerializer,
)


class ConversationCreateView(CreateAPIView):
    """
    Create a private or group conversation.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = CreateConversationSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        conversation = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Conversation created successfully.",
                "data": ConversationSerializer(
                    conversation,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )



class ConversationListView(ListAPIView):
    """
    List all conversations of the authenticated user.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = ConversationListSerializer

    def get_queryset(self):

        return (
            Conversation.objects
            .filter(
                participants__user=self.request.user,
                participants__is_removed=False,
                is_active=True,
            )
            .prefetch_related(
                "participants",
                "messages",
            )
            .distinct()
            .order_by("-updated_at")
        )

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": "Conversations fetched successfully.",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ConversationDetailView(RetrieveAPIView):
    """
    Retrieve a single conversation.
    Only participants can access it.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = ConversationSerializer

    lookup_field = "id"

    def get_queryset(self):

        return (
            Conversation.objects
            .filter(
                participants__user=self.request.user,
                participants__is_removed=False,
                is_active=True,
            )
            .prefetch_related(
                "participants__user",
                "messages__sender",
            )
            .distinct()
        )

    def retrieve(self, request, *args, **kwargs):

        conversation = self.get_object()

        serializer = self.get_serializer(
            conversation,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": "Conversation fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class SendMessageView(CreateAPIView):
    """
    Send a message to a conversation.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = SendMessageSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        message = serializer.save()

        response_serializer = MessageSerializer(
            message,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": "Message sent successfully.",
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class MessageListView(ListAPIView):
    """
    List all messages of a conversation.
    Only conversation participants can access them.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = MessageSerializer

    pagination_class = None

    def get_queryset(self):

        conversation_id = self.kwargs["conversation_id"]

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            is_active=True,
        )

        is_participant = (
            ConversationParticipant.objects.filter(
                conversation=conversation,
                user=self.request.user,
                is_removed=False,
            ).exists()
        )

        if not is_participant:

            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You are not a participant of this conversation."
            )

        return (
            Message.objects
            .filter(
                conversation=conversation,
                is_deleted=False,
            )
            .select_related(
                "sender",
                "reply_to",
            )
            .prefetch_related(
                "attachments",
                "reactions__user",
                "read_receipts__user",
            )
            .order_by("created_at")
        )

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": "Messages fetched successfully.",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class EditMessageView(RetrieveUpdateAPIView):
    """
    Edit a previously sent message.
    Only the sender can edit the message.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = EditMessageSerializer

    queryset = (
        Message.objects
        .select_related(
            "sender",
            "conversation",
        )
    )

    lookup_field = "id"

    def get_object(self):

        message = super().get_object()

        if message.sender != self.request.user:

            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You can edit only your own messages."
            )

        return message

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        message = self.get_object()

        serializer = self.get_serializer(
            message,
            data=request.data,
            partial=partial,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        message = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Message updated successfully.",
                "data": MessageSerializer(
                    message,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class DeleteMessageView(DestroyAPIView):
    """
    Soft delete a message.
    Only the sender can delete the message.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Message.objects
        .select_related(
            "sender",
            "conversation",
        )
    )

    lookup_field = "id"

    def get_object(self):

        message = super().get_object()

        if message.sender != self.request.user:

            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You can delete only your own messages."
            )

        return message

    def destroy(self, request, *args, **kwargs):

        message = self.get_object()

        if message.is_deleted:

            return Response(
                {
                    "success": False,
                    "message": "Message has already been deleted.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        message.is_deleted = True

        message.content = ""

        message.save(
            update_fields=[
                "is_deleted",
                "content",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Message deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )


class ReactMessageView(CreateAPIView):
    """
    Add or update a reaction to a message.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = MessageReactionSerializer

    def create(self, request, *args, **kwargs):

        message = get_object_or_404(
            Message,
            id=self.kwargs["id"],
            is_deleted=False,
        )

        is_participant = (
            ConversationParticipant.objects.filter(
                conversation=message.conversation,
                user=request.user,
                is_removed=False,
            ).exists()
        )

        if not is_participant:

            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You are not a participant of this conversation."
            )

        serializer = self.get_serializer(
            data={
                "message": message.id,
                "emoji": request.data.get("emoji"),
            },
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        reaction = serializer.save(
            message=message,
        )

        return Response(
            {
                "success": True,
                "message": "Reaction updated successfully.",
                "data": MessageReactionSerializer(
                    reaction,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class MarkMessageReadView(CreateAPIView):
    """
    Mark a message as read.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = ReadReceiptSerializer

    def create(self, request, *args, **kwargs):

        message = get_object_or_404(
            Message,
            id=self.kwargs["id"],
            is_deleted=False,
        )

        is_participant = (
            ConversationParticipant.objects.filter(
                conversation=message.conversation,
                user=request.user,
                is_removed=False,
            ).exists()
        )

        if not is_participant:

            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You are not a participant of this conversation."
            )

        serializer = self.get_serializer(
            data={
                "message": message.id,
            },
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        receipt = serializer.save(
            message=message,
        )

        return Response(
            {
                "success": True,
                "message": "Message marked as read.",
                "data": ReadReceiptSerializer(
                    receipt,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=status.HTTP_200_OK,
        )