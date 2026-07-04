import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ConversationType(models.TextChoices):
    PRIVATE = "private", "Private"
    GROUP = "group", "Group"


class ParticipantRole(models.TextChoices):
    MEMBER = "member", "Member"
    ADMIN = "admin", "Admin"
    OWNER = "owner", "Owner"


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"
    AUDIO = "audio", "Audio"
    VOICE = "voice", "Voice"
    DOCUMENT = "document", "Document"
    STICKER = "sticker", "Sticker"
    LOCATION = "location", "Location"
    CONTACT = "contact", "Contact"

class MessageStatus(models.TextChoices):
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    READ = "read", "Read"



class Conversation(models.Model):
    """
    Represents a private or group conversation.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conversation_type = models.CharField(
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.PRIVATE,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    image = models.ImageField(
        upload_to="chat/conversations/",
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_conversations",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

        indexes = [
            models.Index(fields=["conversation_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["is_active"]),
        ]

    def clean(self):
        super().clean()

        if (
            self.conversation_type == ConversationType.PRIVATE
            and self.title
        ):
            raise ValidationError(
                "Private conversations cannot have a title."
            )

        if (
            self.conversation_type == ConversationType.GROUP
            and not (self.title or "").strip()
        ):
            raise ValidationError(
                "Group conversations must have a title."
            )

    def __str__(self):
        if self.conversation_type == ConversationType.PRIVATE:
            return f"Private Chat ({self.id})"

        return self.title



class ConversationParticipant(models.Model):
    """
    Stores a user's membership and settings for a conversation.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    role = models.CharField(
        max_length=20,
        choices=ParticipantRole.choices,
        default=ParticipantRole.MEMBER,
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_read_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )

    last_read_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    is_muted = models.BooleanField(
        default=False,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    is_pinned = models.BooleanField(
        default=False,
    )

    is_removed = models.BooleanField(
        default=False,
    )

    nickname = models.CharField(
        max_length=100,
        blank=True,
    )

    class Meta:

        ordering = ["joined_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "conversation",
                    "user",
                ],
                name="unique_conversation_participant",
            )
        ]

        indexes = [
            models.Index(fields=["conversation"]),
            models.Index(fields=["user"]),
            models.Index(fields=["role"]),
            models.Index(fields=["joined_at"]),
            models.Index(fields=["is_removed"]),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.conversation.id}"

class Message(models.Model):
    """
    Represents a message inside a conversation.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )

    content = models.TextField(
        blank=True,
    )

    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.SENT,
        db_index=True,
    )

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="replies",
    )

    is_edited = models.BooleanField(
        default=False,
    )

    edited_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = ["id"]

        indexes = [

            models.Index(
                fields=[
                    "conversation",
                    "created_at",
                ]
            ),

            models.Index(
                fields=[
                    "conversation",
                    "is_deleted",
                ]
            ),

            models.Index(
                fields=[
                    "sender",
                    "created_at",
                ]
            ),

            models.Index(
                fields=[
                    "message_type",
                ]
            ),

            models.Index(
                fields=[
                    "reply_to",
                ]
            ),

            models.Index(
                fields=[
                    "status",
                ]
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.message_type == MessageType.TEXT
            and not (self.content or "").strip()
        ):
            raise ValidationError(
                "Text message cannot be empty."
            )

    @property
    def has_attachment(self):
        return self.attachments.exists()

    @property
    def is_reply(self):
        return self.reply_to is not None

    @property
    def is_media(self):
        return self.message_type in [
            MessageType.IMAGE,
            MessageType.VIDEO,
            MessageType.AUDIO,
            MessageType.VOICE,
            MessageType.DOCUMENT,
            MessageType.STICKER,
        ]

    def __str__(self):
        preview = (
            self.content[:30]
            if self.content
            else self.message_type
        )

        return f"{self.sender.username}: {preview}"



class MessageAttachment(models.Model):
    """
    Stores media and document attachments for a message.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to="chat/attachments/",
    )

    thumbnail = models.ImageField(
        upload_to="chat/thumbnails/",
        blank=True,
        null=True,
    )

    mime_type = models.CharField(
        max_length=150,
    )

    file_size = models.BigIntegerField()

    duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Duration in seconds for audio/video.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["mime_type"]),
        ]

    def __str__(self):
        return f"{self.message.id} - {self.mime_type}"



class MessageReaction(models.Model):
    """
    Stores emoji reactions on messages.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_reactions",
    )

    emoji = models.CharField(
        max_length=20,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "message",
                    "user",
                ],
                name="unique_user_message_reaction",
            )
        ]

        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji}"



class ReadReceipt(models.Model):
    """
    Tracks when a participant reads a message.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="read_receipts",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="read_receipts",
    )

    read_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["read_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "message",
                    "user",
                ],
                name="unique_message_read_receipt",
            )
        ]

        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["user"]),
            models.Index(fields=["read_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} read {self.message.id}"



class DeletedMessage(models.Model):
    """
    Supports 'Delete for Me'.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="deleted_for",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deleted_messages",
    )

    deleted_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = ["-deleted_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "message",
                    "user",
                ],
                name="unique_deleted_message",
            )
        ]

        indexes = [
            models.Index(fields=["message"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} deleted message {self.message.id}"