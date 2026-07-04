from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework import status
from rest_framework.generics import (
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    ListAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Profile,
    PrivacySetting,
    BlockedUser,
)

from .serializers import (
    ProfileSerializer,
    UpdateProfileSerializer,
    PublicProfileSerializer,
    PrivacySettingSerializer,
    UserSearchSerializer,
    BlockedUserSerializer,
)


# --------------------------------------------------
# My Profile
# --------------------------------------------------

class MyProfileView(RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user
        ) 
        return profile

    def get_serializer_class(self):

        if self.request.method in ["PUT", "PATCH"]:
            return UpdateProfileSerializer

        return ProfileSerializer

    def retrieve(self, request, *args, **kwargs):

        serializer = self.get_serializer(self.get_object())

        return Response(
            {
                "success": True,
                "message": "Profile fetched successfully.",
                "data": serializer.data,
            }
        )

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        profile = self.get_object()

        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "data": ProfileSerializer(profile).data,
            }
        )


# --------------------------------------------------
# Public Profile
# --------------------------------------------------

class PublicProfileView(RetrieveAPIView):
    """
    Retrieve a public profile by username.
    """

    serializer_class = PublicProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    def get_object(self):
        profile = get_object_or_404(
            Profile.objects.select_related(
                "user",
                "user__presence",
                "user__privacy",
            ),
            user__username=self.kwargs["username"],
        )

        if not profile.is_public:
            raise PermissionDenied("This profile is private.")

        return profile
# --------------------------------------------------
# Search Users
# --------------------------------------------------

class UserSearchView(ListAPIView):
    """
    Search public users by username, first name,
    last name or location.
    """

    serializer_class = UserSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()

        queryset = (
            Profile.objects
            .select_related(
                "user",
                "user__presence",
            )
            .exclude(user=self.request.user)
            .filter(is_public=True)
        )

        if query:
            queryset = queryset.filter(
                Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(location__icontains=query)
            )

        return queryset.order_by("user__username")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(
            {
                "success": True,
                "message": "Users fetched successfully.",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

# --------------------------------------------------
# Privacy APIs
# --------------------------------------------------

class PrivacyView(RetrieveUpdateAPIView):
    """
    Retrieve and update the authenticated user's privacy settings.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PrivacySettingSerializer

    def get_object(self):
        privacy, _ = PrivacySetting.objects.get_or_create(
            user=self.request.user
        )
        return privacy

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())

        return Response(
            {
                "success": True,
                "message": "Privacy settings fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        privacy = self.get_object()

        serializer = self.get_serializer(
            privacy,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Privacy settings updated successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

# --------------------------------------------------
# Block User
# --------------------------------------------------

class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        username = request.data.get("username")

        if not username:
            raise ValidationError(
                {"username": "Username is required."}
            )

        profile = get_object_or_404(
            Profile,
            user__username=username,
        )

        if profile.user == request.user:
            raise ValidationError(
                "You cannot block yourself."
            )

        blocked, created = BlockedUser.objects.get_or_create(
            user=request.user,
            blocked_user=profile.user,
        )

        if not created:
            return Response(
                {
                    "success": False,
                    "message": "User is already blocked.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": f"{username} blocked successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------
# Unblock User
# --------------------------------------------------

class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, username):

        profile = get_object_or_404(
            Profile,
            user__username=username,
        )

        blocked = BlockedUser.objects.filter(
            user=request.user,
            blocked_user=profile.user,
        )

        if not blocked.exists():
            return Response(
                {
                    "success": False,
                    "message": "User is not blocked.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        blocked.delete()

        return Response(
            {
                "success": True,
                "message": "User unblocked successfully.",
            }
        )


# --------------------------------------------------
# Blocked Users List
# --------------------------------------------------

class BlockedUsersView(ListAPIView):
    """
    List all blocked users.
    """

    serializer_class = BlockedUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            BlockedUser.objects
            .select_related(
                "blocked_user",
                "blocked_user__profile",
            )
            .filter(user=self.request.user)
            .order_by("-blocked_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(
            {
                "success": True,
                "message": "Blocked users fetched successfully.",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )