
from django.db.models import Max
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from django.contrib.sessions.models import Session
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@receiver(pre_save, sender=AccountDetails)
def create_account_no(sender, instance, *args, **kwargs):
    # checks if user has an account number and user is not staff or superuser
    if not instance.account_no and not (instance.user.is_staff or instance.user.is_superuser):
        # gets the largest account number
        largest = AccountDetails.objects.all().aggregate(
            Max("account_no")
            )['account_no__max']

        if largest:
            # creates new account number
            instance.account_no = largest + 1
        else:
            # if there is no other user, sets users account number to 10000000.
            instance.account_no = 10000000


@receiver(post_save, sender=User)
def post_save_create_profile(sender, instance, created, *args, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def terminate_sessions_on_ban(sender, instance, **kwargs):
    if instance.is_banned:
        Session.objects.filter(session_key__in=instance.session_set.values_list('session_key', flat=True)).delete()



@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        subject = 'Welcome to Orbit Stock Index'
        message = render_to_string('accounts/emails/welcome_email.html', {'user': instance})

        send_mail(
            subject=subject,
            message="Welcome to Orbit Stock Index!",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.email],
            fail_silently=False,
            html_message=message  # Send the HTML email
        )



@receiver(post_save, sender=Investment)
def send_investment_confirmation_email(sender, instance, created, **kwargs):
    # Check if the investment is newly created and has a 'pending' status
    if created and instance.status == 'pending':
        # Get user email
        user_email = instance.user.email

        # Context for rendering the email template
        context = {
            'investment': instance
        }

        # Render HTML email content
        html_content = render_to_string('accounts/emails/investment_notification_email.html', context)
        text_content = strip_tags(html_content)  # Fallback for plain text email clients

        # Send email
        send_mail(
            subject='Investment Confirmation - Pending',
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_content,
            fail_silently=False,
        )






def send_investment_email(investment, status, profit=None):
    subject = f"Investment {status}"
    context = {
        'investment': investment,
        'profit': profit,
    }
    html_message = render_to_string(f'accounts/emails/investment_{status.lower()}.html', context)
    plain_message = strip_tags(html_message)
    print(f"HTML Message: {html_message}")  # Debug print
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = investment.user.email

    send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)


@receiver(post_save, sender=Investment)
def send_admin_investment_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        subject = f"New Investment by {user.get_full_name()} ({user.username})"
        message = (
            f"User Details:\n"
            f"Full Name: {user.get_full_name()}\n"
            f"Username: {user.username}\n"
            f"Email: {user.email}\n\n"
            f"Investment Details:\n"
            f"Amount: {instance.amount}\n"
            f"Schema: {dict(instance.SCHEMA_CHOICES).get(instance.schema_id)}\n"
            f"Status: {instance.status}\n"
            f"Created At: {instance.created_at}\n"
        )
        recipient_list = ['orbitstockindex@gmail.com']
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
