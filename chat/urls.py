from django.urls import path

from .views import (
    ConversationCreateView,
    ConversationListView,
    ConversationDetailView,
    SendMessageView,
    MessageListView,
    EditMessageView,
    DeleteMessageView,
    ReactMessageView,
    MarkMessageReadView,
)

app_name = "chat"

urlpatterns = [

    path(
        "conversations/",
        ConversationListView.as_view(),
        name="conversation-list",
    ),

    path(
        "conversations/create/",
        ConversationCreateView.as_view(),
        name="conversation-create",
    ),

    path(
        "conversations/<uuid:id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),

    path(
        "conversations/<uuid:conversation_id>/messages/",
        MessageListView.as_view(),
        name="message-list",
    ),


    path(
        "messages/send/",
        SendMessageView.as_view(),
        name="message-send",
    ),

    path(
        "messages/<int:id>/edit/",
        EditMessageView.as_view(),
        name="message-edit",
    ),

    path(
        "messages/<int:id>/delete/",
        DeleteMessageView.as_view(),
        name="message-delete",
    ),

    path(
        "messages/<int:id>/reaction/",
        ReactMessageView.as_view(),
        name="message-reaction",
    ),

    path(
        "messages/<int:id>/read/",
        MarkMessageReadView.as_view(),
        name="message-read",
    ),
]