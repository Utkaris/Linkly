from django.urls import path

from .views import (
    MyProfileView,
    PublicProfileView,
    UserSearchView,
    PrivacyView,
    BlockUserView,
    UnblockUserView,
    BlockedUsersView,
)

app_name = "users"

urlpatterns = [

    # My Profile
    path(
        "me/",
        MyProfileView.as_view(),
        name="my-profile",
    ),

    # Search
    path(
        "search/",
        UserSearchView.as_view(),
        name="search-users",
    ),

    # Privacy
    path(
        "privacy/",
        PrivacyView.as_view(),
        name="privacy",
    ),

    # Block User
    path(
        "block/",
        BlockUserView.as_view(),
        name="block-user",
    ),

    path(
        "blocked/",
        BlockedUsersView.as_view(),
        name="blocked-users",
    ),

    path(
        "block/<str:username>/",
        UnblockUserView.as_view(),
        name="unblock-user",
    ),

    # Public Profile (KEEP LAST)
    path(
        "<str:username>/",
        PublicProfileView.as_view(),
        name="public-profile",
    ),
]