from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User

from .models import (
    Profile,
    Presence,
    PrivacySetting,
)


@receiver(post_save, sender=User)
def create_user_related_objects(sender, instance, created, **kwargs):
    """
    Automatically create related user objects
    whenever a new account is created.
    """
    if created:
        Profile.objects.create(user=instance)

        Presence.objects.create(user=instance)

        PrivacySetting.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save profile whenever user is saved.
    """
    if hasattr(instance, "profile"):
        instance.profile.save()