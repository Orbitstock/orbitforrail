from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from accounts.models import AccountDetails, Profile
from django.conf import settings

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=AccountDetails)
def post_save_create_profile(sender, instance, created, *args, **kwargs):
    if created and instance.user:
        # Check if a profile already exists for the user
        profile, created = Profile.objects.get_or_create(user=instance.user)

        # If the profile is created, set the recommended_by field
        if created and instance.user.account.upline:
            recommended_by_user = instance.user.account.upline
            profile.recommended_by = recommended_by_user
            profile.save()
