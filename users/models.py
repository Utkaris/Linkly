from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class GenderChoices(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"
    NOT_SPECIFIED = "N", "Prefer not to say"


class PrivacyChoices(models.TextChoices):
    EVERYONE = "everyone", "Everyone"
    CONTACTS = "contacts", "My Contacts"
    NOBODY = "nobody", "Nobody"


class ThemeChoices(models.TextChoices):
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"
    SYSTEM = "system", "System"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    avatar = models.ImageField(
        upload_to="users/avatars/",
        default="users/avatars/default.png",
    )

    cover_photo = models.ImageField(
        upload_to="users/covers/",
        blank=True,
        null=True,
    )

    bio = models.CharField(
        max_length=150,
        blank=True,
    )

    status = models.CharField(
        max_length=100,
        default="Available",
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9]{10,15}$",
                message="Enter a valid phone number.",
            )
        ],
    )

    website = models.URLField(blank=True)

    location = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True,
    )

    gender = models.CharField(
        max_length=1,
        choices=GenderChoices.choices,
        default=GenderChoices.NOT_SPECIFIED,
    )

    theme = models.CharField(
        max_length=10,
        choices=ThemeChoices.choices,
        default=ThemeChoices.SYSTEM,
    )

    is_public = models.BooleanField(default=True)

    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return self.user.username

    @property
    def profile_completion(self):
        completed = 0

        if self.avatar:
            completed += 15

        if self.cover_photo:
            completed += 15

        if self.bio:
            completed += 15

        if self.phone_number:
            completed += 15

        if self.location:
            completed += 10

        if self.website:
            completed += 10

        if self.date_of_birth:
            completed += 10

        if self.gender != GenderChoices.NOT_SPECIFIED:
            completed += 10

        return completed


class Presence(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="presence",
    )

    is_online = models.BooleanField(default=False)

    last_seen = models.DateTimeField(
        blank=True,
        null=True,
    )

    last_active = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Presence"
        verbose_name_plural = "Presence"
        indexes = [
            models.Index(fields=["is_online"]),
            models.Index(fields=["last_seen"]),
        ]

    def __str__(self):
        return self.user.username


class PrivacySetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="privacy",
    )

    last_seen = models.CharField(
        max_length=20,
        choices=PrivacyChoices.choices,
        default=PrivacyChoices.EVERYONE,
    )

    profile_photo = models.CharField(
        max_length=20,
        choices=PrivacyChoices.choices,
        default=PrivacyChoices.EVERYONE,
    )

    status = models.CharField(
        max_length=20,
        choices=PrivacyChoices.choices,
        default=PrivacyChoices.EVERYONE,
    )

    read_receipts = models.BooleanField(default=True)

    allow_messages_from = models.CharField(
        max_length=20,
        choices=PrivacyChoices.choices,
        default=PrivacyChoices.EVERYONE,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Privacy"


class BlockedUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_users",
    )

    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by",
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
    )

    blocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-blocked_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "blocked_user"],
                name="unique_blocked_user",
            )
        ]

    def clean(self):
        if self.user == self.blocked_user:
            raise ValidationError(
                "You cannot block yourself."
            )

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"