from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """
    Reserved for future use.

    Later we will:
    - Create Profile
    - Send Welcome Email
    - Create Notification Settings
    """
    if created:
        pass