from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageReaction,
    ReadReceipt,
    MessageType,
    MessageStatus,
    ConversationType,
    ParticipantRole,
)

User = get_user_model()

class ConversationParticipantSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True,
    )

    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True,
    )

    avatar = serializers.ImageField(
        source="user.profile.avatar",
        read_only=True,
    )

    is_online = serializers.BooleanField(
        source="user.presence.is_online",
        read_only=True,
    )

    class Meta:

        model = ConversationParticipant

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "role",
            "nickname",
            "is_online",
            "joined_at",
            "is_muted",
            "is_archived",
            "is_pinned",
        ]

class ConversationSerializer(serializers.ModelSerializer):

    participants = ConversationParticipantSerializer(
        many=True,
        read_only=True,
    )

    created_by = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:

        model = Conversation

        fields = [
            "id",
            "conversation_type",
            "title",
            "description",
            "image",
            "created_by",
            "participants",
            "is_active",
            "created_at",
            "updated_at",
        ]


class CreateConversationSerializer(serializers.Serializer):
    """
    Serializer for creating private and group conversations.
    """

    conversation_type = serializers.ChoiceField(
        choices=ConversationType.choices
    )

    participants = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )

    title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    image = serializers.ImageField(
        required=False,
        allow_null=True,
    )

    def validate_participants(self, value):

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate participants are not allowed."
            )

        users = User.objects.filter(id__in=value)

        if users.count() != len(value):
            raise serializers.ValidationError(
                "One or more users do not exist."
            )

        return value

    def validate(self, attrs):

        conversation_type = attrs.get("conversation_type")

        if (
            conversation_type == ConversationType.PRIVATE
            and len(attrs["participants"]) != 1
        ):
            raise serializers.ValidationError(
                {
                    "participants":
                    "Private conversation must contain exactly one participant."
                }
            )

        if (
            conversation_type == ConversationType.GROUP
            and not (attrs.get("title") or "").strip()
        ):
            raise serializers.ValidationError(
                {
                    "title":
                    "Group conversation requires a title."
                }
            )

        return attrs

    def create(self, validated_data):

        request = self.context["request"]

        participant_ids = validated_data.pop("participants")

        participant_ids = [
            user_id
            for user_id in participant_ids
            if user_id != request.user.id
        ]

        conversation = Conversation.objects.create(
            created_by=request.user,
            **validated_data,
        )

        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user,
            role=ParticipantRole.OWNER,
        )

        users = User.objects.filter(
            id__in=participant_ids
        )

        for user in users:

            ConversationParticipant.objects.create(
                conversation=conversation,
                user=user,
                role=ParticipantRole.MEMBER,
            )

        return conversation


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Serializer used in chat sidebar.
    """

    last_message = serializers.SerializerMethodField()

    participant_count = serializers.SerializerMethodField()

    unread_count = serializers.SerializerMethodField()

    class Meta:

        model = Conversation

        fields = [
            "id",
            "conversation_type",
            "title",
            "image",
            "updated_at",
            "participant_count",
            "last_message",
            "unread_count",
        ]

    def get_participant_count(self, obj):

        return obj.participants.filter(
            is_removed=False
        ).count()

    def get_last_message(self, obj):

        message = (
            obj.messages
            .filter(is_deleted=False)
            .select_related("sender")
            .last()
        )

        if not message:
            return None

        return {
            "id": message.id,
            "sender": message.sender.username,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at,
        }

    def get_unread_count(self, obj):

        request = self.context.get("request")

        if request is None:
            return 0

        participant = obj.participants.filter(
            user=request.user
        ).first()

        if participant is None:
            return 0

        queryset = obj.messages.filter(
            is_deleted=False,
        )

        if participant.last_read_message:

            queryset = queryset.filter(
                id__gt=participant.last_read_message.id
            )

        return queryset.exclude(
            sender=request.user
        ).count()


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for message attachments.
    """

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MessageAttachment

        fields = [
            "id",
            "file",
            "file_url",
            "thumbnail",
            "mime_type",
            "file_size",
            "duration",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "mime_type",
            "file_size",
            "created_at",
        ]

    def get_file_url(self, obj):

        request = self.context.get("request")

        if not obj.file:
            return None

        if request:
            return request.build_absolute_uri(
                obj.file.url
            )

        return obj.file.url

    def validate_file(self, value):

        max_size = 100 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "File size cannot exceed 100 MB."
            )

        return value

    def create(self, validated_data):

        uploaded_file = validated_data["file"]

        validated_data["mime_type"] = uploaded_file.content_type

        validated_data["file_size"] = uploaded_file.size

        return MessageAttachment.objects.create(
            **validated_data
        )



class MessageReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for adding or updating reactions
    on a message.
    """

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:

        model = MessageReaction

        fields = [
            "id",
            "message",
            "user",
            "username",
            "emoji",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "created_at",
        ]

    def validate_emoji(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Emoji cannot be empty."
            )

        if len(value) > 32:
            raise serializers.ValidationError(
                "Emoji is too long."
            )

        return value

    def create(self, validated_data):

        request = self.context["request"]

        message = validated_data["message"]

        reaction, created = (
            MessageReaction.objects.update_or_create(
                message=message,
                user=request.user,
                defaults={
                    "emoji": validated_data["emoji"],
                },
            )
        )

        return reaction



class ReadReceiptSerializer(serializers.ModelSerializer):
    """
    Serializer for marking a message as read.
    """

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:

        model = ReadReceipt

        fields = [
            "id",
            "message",
            "user",
            "username",
            "read_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "read_at",
        ]

    def validate(self, attrs):

        request = self.context["request"]

        message = attrs["message"]

        if message.sender == request.user:
            raise serializers.ValidationError(
                "You cannot mark your own message as read."
            )

        return attrs

    def create(self, validated_data):

        request = self.context["request"]

        message = validated_data["message"]

        receipt, created = (
            ReadReceipt.objects.get_or_create(
                message=message,
                user=request.user,
            )
        )

        participant = (
            ConversationParticipant.objects.filter(
                conversation=message.conversation,
                user=request.user,
            ).first()
        )

        if participant:

            participant.last_read_message = message
            participant.save(
                update_fields=[
                    "last_read_message",
                ]
            )

        if (
            message.status != MessageStatus.READ
        ):
            message.status = MessageStatus.READ
            message.save(
                update_fields=[
                    "status",
                ]
            )

        return receipt


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving chat messages.
    """

    sender = serializers.CharField(
        source="sender.username",
        read_only=True,
    )

    sender_id = serializers.IntegerField(
        source="sender.id",
        read_only=True,
    )

    sender_avatar = serializers.ImageField(
        source="sender.profile.avatar",
        read_only=True,
    )

    attachments = MessageAttachmentSerializer(
        many=True,
        read_only=True,
    )

    reactions = MessageReactionSerializer(
        many=True,
        read_only=True,
    )

    read_receipts = ReadReceiptSerializer(
        many=True,
        read_only=True,
    )

    reply_to = serializers.SerializerMethodField()

    is_mine = serializers.SerializerMethodField()

    class Meta:

        model = Message

        fields = [
            "id",
            "conversation",
            "sender_id",
            "sender",
            "sender_avatar",
            "content",
            "message_type",
            "status",
            "reply_to",
            "attachments",
            "reactions",
            "read_receipts",
            "is_edited",
            "edited_at",
            "is_deleted",
            "is_mine",
            "created_at",
            "updated_at",
        ]

    def get_reply_to(self, obj):

        if not obj.reply_to:
            return None

        return {
            "id": obj.reply_to.id,
            "sender": obj.reply_to.sender.username,
            "content": obj.reply_to.content,
            "message_type": obj.reply_to.message_type,
        }

    def get_is_mine(self, obj):

        request = self.context.get("request")

        if request is None:
            return False

        return obj.sender == request.user



class SendMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for sending a new message.
    """

    class Meta:

        model = Message

        fields = [
            "conversation",
            "content",
            "message_type",
            "reply_to",
        ]

    def validate(self, attrs):

        request = self.context["request"]

        conversation = attrs["conversation"]

        if not ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user,
            is_removed=False,
        ).exists():

            raise serializers.ValidationError(
                "You are not a participant of this conversation."
            )

        if (
            attrs["message_type"] == MessageType.TEXT
            and not (attrs.get("content") or "").strip()
        ):
            raise serializers.ValidationError(
                {
                    "content":
                    "Text message cannot be empty."
                }
            )

        reply = attrs.get("reply_to")

        if reply:

            if reply.conversation != conversation:

                raise serializers.ValidationError(
                    {
                        "reply_to":
                        "Reply message must belong to the same conversation."
                    }
                )

        return attrs

    def create(self, validated_data):

        request = self.context["request"]

        message = Message.objects.create(
            sender=request.user,
            **validated_data,
        )

        conversation = message.conversation

        conversation.save(
            update_fields=[
                "updated_at",
            ]
        )

        return message



class EditMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for editing a message.
    """

    class Meta:

        model = Message

        fields = [
            "content",
        ]

    def validate_content(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "Message cannot be empty."
            )

        return value

    def update(self, instance, validated_data):

        request = self.context["request"]

        if instance.sender != request.user:

            raise serializers.ValidationError(
                "You can edit only your own messages."
            )

        if instance.is_deleted:

            raise serializers.ValidationError(
                "Deleted messages cannot be edited."
            )

        instance.content = validated_data["content"]

        instance.is_edited = True

        instance.edited_at = timezone.now()

        instance.save(
            update_fields=[
                "content",
                "is_edited",
                "edited_at",
                "updated_at",
            ]
        )

        return instance