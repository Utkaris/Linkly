from django.core.files.images import get_image_dimensions
from rest_framework import serializers

from .models import (
    Profile,
    Presence,
    PrivacySetting,
    BlockedUser,
)


class PresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presence
        fields = (
            "is_online",
            "last_seen",
            "last_active",
        )
        read_only_fields = fields


class PrivacySettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacySetting
        exclude = (
            "id",
            "user",
            "created_at",
            "updated_at",
        )


class ProfileSerializer(serializers.ModelSerializer):
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

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    profile_completion = serializers.ReadOnlyField()

    presence = PresenceSerializer(
        read_only=True,
        source="user.presence",
    )

    privacy = PrivacySettingSerializer(
        read_only=True,
        source="user.privacy",
    )

    class Meta:
        model = Profile

        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "cover_photo",
            "bio",
            "status",
            "phone_number",
            "website",
            "location",
            "date_of_birth",
            "gender",
            "theme",
            "is_public",
            "verified",
            "profile_completion",
            "presence",
            "privacy",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "verified",
            "profile_completion",
            "created_at",
            "updated_at",
        )


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile

        fields = (
            "avatar",
            "cover_photo",
            "bio",
            "status",
            "phone_number",
            "website",
            "location",
            "date_of_birth",
            "gender",
            "theme",
            "is_public",
        )

    def validate_avatar(self, value):
        if not value:
            return value

        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Avatar size cannot exceed 5 MB."
            )

        try:
            width, height = get_image_dimensions(value)
        except Exception:
            raise serializers.ValidationError(
                "Invalid image."
            )

        if width < 200 or height < 200:
            raise serializers.ValidationError(
                "Minimum avatar resolution is 200x200."
            )

        return value

    def validate_cover_photo(self, value):
        if not value:
            return value

        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Cover photo cannot exceed 10 MB."
            )

        return value

    def validate_bio(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                "Bio cannot exceed 150 characters."
            )

        return value


class PublicProfileSerializer(serializers.ModelSerializer):
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

    is_online = serializers.BooleanField(
        source="user.presence.is_online",
        read_only=True,
    )

    last_seen = serializers.DateTimeField(
        source="user.presence.last_seen",
        read_only=True,
    )

    class Meta:
        model = Profile

        fields = (
            "username",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "status",
            "location",
            "verified",
            "is_online",
            "last_seen",
        )


class UserSearchSerializer(serializers.ModelSerializer):
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

    is_online = serializers.BooleanField(
        source="user.presence.is_online",
        read_only=True,
    )

    class Meta:
        model = Profile

        fields = (
            "username",
            "first_name",
            "last_name",
            "avatar",
            "status",
            "verified",
            "is_online",
        )


class BlockedUserSerializer(serializers.ModelSerializer):
    blocked_username = serializers.CharField(
        source="blocked_user.username",
        read_only=True,
    )

    blocked_avatar = serializers.ImageField(
        source="blocked_user.profile.avatar",
        read_only=True,
    )

    class Meta:
        model = BlockedUser

        fields = (
            "id",
            "blocked_user",
            "blocked_username",
            "blocked_avatar",
            "reason",
            "blocked_at",
        )

        read_only_fields = (
            "id",
            "blocked_at",
        )