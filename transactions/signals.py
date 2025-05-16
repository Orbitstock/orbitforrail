from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Withdrawal, Payment, CryptoWITHDRAW
from datetime import datetime
import pytz
from django.template.loader import render_to_string
import logging



import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

from django.db.models.signals import pre_save
from django.dispatch import receiver




@receiver(post_save, sender=Withdrawal)
def update_balance_and_send_initial_email(sender, instance, created, **kwargs):
    # Adjust user balance based on status
    if instance.status in ['COMPLETED', 'COMPLETE']:
        instance.user.balance -= instance.amount
    elif instance.status == 'CANCELLED':
        instance.user.balance += instance.amount
    instance.user.save()

    # Send email for newly created withdrawal with "PENDING" status
    if created and instance.status == 'PENDING':
        subject = 'Transfer Update'
        template_name = 'transactions/emails/withdrawal_pending.html'
        message = render_to_string(template_name, {'withdrawal': instance})
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email], html_message=message)
            logger.info(f'Withdrawal email sent to {instance.user.email} for status {instance.status}')
        except Exception as e:
            logger.error(f'Error sending withdrawal email: {e}')


@receiver(pre_save, sender=Withdrawal)
def send_withdrawal_email(sender, instance, **kwargs):
    # Check if the instance is being updated (not created)
    if instance.pk:
        # Fetch the old status from the database
        old_instance = Withdrawal.objects.get(pk=instance.pk)
        old_status = old_instance.status
        
        # Compare old and new status
        if old_status != instance.status:
            subject = 'Transfer Update'
            template_map = {
                'PENDING': 'transactions/emails/withdrawal_pending.html',
                'COMPLETED': 'transactions/emails/withdrawal_completed.html',
                'CANCELLED': 'transactions/emails/withdrawal_cancelled.html',
                'DECLINED': 'transactions/emails/withdrawal_declined.html'
            }
            template_name = template_map.get(instance.status)
            if template_name:
                message = render_to_string(template_name, {'withdrawal': instance})
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email], html_message=message)
                    logger.info(f'Withdrawal email sent to {instance.user.email} for status {instance.status}')
                except Exception as e:
                    logger.error(f'Error sending withdrawal email: {e}')



@receiver(post_save, sender=Payment)
def handle_payment_creation_and_update(sender, instance, created, **kwargs):
    # Send email for newly created payment with "PENDING" status
    if created and instance.status == 'PENDING':
        subject = 'Deposit Update'
        template_name = 'transactions/emails/payment_pending.html'
        message = render_to_string(template_name, {'payment': instance})
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email], html_message=message)
            logger.info(f'Payment email sent to {instance.user.email} for status {instance.status}')
        except Exception as e:
            logger.error(f'Error sending payment email: {e}')




@receiver(pre_save, sender=Payment)
def send_payment_email(sender, instance, **kwargs):
    # Check if the instance is being updated (not created)
    if instance.pk:
        # Fetch the old status from the database
        old_instance = Payment.objects.get(pk=instance.pk)
        old_status = old_instance.status

        # Compare old and new status
        if old_status != instance.status:
            subject = 'Deposit Update'
            template_map = {
                'PENDING': 'transactions/emails/payment_pending.html',
                'COMPLETE': 'transactions/emails/payment_complete.html',
                'CANCELLED': 'transactions/emails/payment_cancelled.html',
                'DECLINED': 'transactions/emails/payment_declined.html'
            }
            template_name = template_map.get(instance.status)
            if template_name:
                message = render_to_string(template_name, {'payment': instance})
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email], html_message=message)
                    logger.info(f'Payment email sent to {instance.user.email} for status {instance.status}')
                except Exception as e:
                    logger.error(f'Error sending payment email: {e}')


@receiver(post_save, sender=CryptoWITHDRAW)
def handle_crypto_withdraw_creation_and_update(sender, instance, created, **kwargs):
    # Send email for newly created crypto withdrawal with "PENDING" status
    if created and instance.status == 'PENDING':
        subject = 'Crypto Withdrawal Update'
        template_name = 'transactions/emails/crypto_withdraw_pending.html'
        message = render_to_string(template_name, {'crypto_withdraw': instance})
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email], html_message=message)
            logger.info(f'CryptoWITHDRAW email sent to {instance.user.email} for status {instance.status}')
        except Exception as e:
            logger.error(f'Error sending crypto_withdraw email: {e}')




@receiver(pre_save, sender=CryptoWITHDRAW)
def send_crypto_withdraw_email(sender, instance, **kwargs):
    # Check if the instance is being updated (not created)
    if instance.pk:
        # Fetch the old status from the database
        old_instance = CryptoWITHDRAW.objects.get(pk=instance.pk)
        old_status = old_instance.status

        # Compare old and new status
        if old_status != instance.status:
            subject = 'Crypto Withdrawal Update'
            template_map = {
                'PENDING': 'transactions/emails/crypto_withdraw_pending.html',
                'COMPLETE': 'transactions/emails/crypto_withdraw_complete.html',
                'CANCELLED': 'transactions/emails/crypto_withdraw_cancelled.html',
                'DECLINED': 'transactions/emails/crypto_withdraw_declined.html'
            }
            template_name = template_map.get(instance.status)
            if template_name:
                message = render_to_string(template_name, {'crypto_withdraw': instance})
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.user.email], html_message=message)
                    logger.info(f'CryptoWITHDRAW email sent to {instance.user.email} for status {instance.status}')
                except Exception as e:
                    logger.error(f'Error sending crypto_withdraw email: {e}')

                    

            


logger = logging.getLogger(__name__)

def send_email(subject, message, recipient_list):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=message)
        logger.info(f'Email sent to {recipient_list}')
    except Exception as e:
        logger.error(f'Error sending email: {e}')



def format_timestamp(timestamp):
    # Convert the timestamp to the server's timezone
    local_tz = pytz.timezone(settings.TIME_ZONE)
    local_time = timestamp.astimezone(local_tz)
    return local_time.strftime('%d %B %Y, %I:%M %p')

@receiver(post_save, sender=Withdrawal)
def send_admin_withdrawal_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        subject = f"New Withdrawal by {user.get_full_name()} ({user.username})"
        message = (
            f"User Details:\n"
            f"Full Name: {user.get_full_name()}\n"
            f"Username: {user.username}\n"
            f"Email: {user.email}\n\n"
            f"Withdrawal Details:\n"
            f"Amount: {instance.amount}\n"
            f"Target: {instance.target}\n"
            f"Target Email: {instance.target_email}\n"
            f"Status: {instance.status}\n"
            f"Timestamp: {format_timestamp(instance.timestamp)}\n"
        )
        recipient_list = ['orbitstockindex@gmail.com']
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)

@receiver(post_save, sender=Payment)
def send_admin_payment_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        subject = f"New Payment by {user.get_full_name()} ({user.username})"
        message = (
            f"User Details:\n"
            f"Full Name: {user.get_full_name()}\n"
            f"Username: {user.username}\n"
            f"Email: {user.email}\n\n"
            f"Payment Details:\n"
            f"Amount: {instance.amount}\n"
            f"Payment Method: {instance.payment_method}\n"
            f"Status: {instance.status}\n"
            f"Timestamp: {format_timestamp(instance.timestamp)}\n"
        )
        recipient_list = ['orbitstockindex@gmail.com']
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)

@receiver(post_save, sender=CryptoWITHDRAW)
def send_admin_crypto_withdrawal_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        subject = f"New Crypto Withdrawal by {user.get_full_name()} ({user.username})"
        message = (
            f"User Details:\n"
            f"Full Name: {user.get_full_name()}\n"
            f"Username: {user.username}\n"
            f"Email: {user.email}\n\n"
            f"Crypto Withdrawal Details:\n"
            f"Amount: {instance.amount}\n"
            f"Payment Method: {instance.payment_method}\n"
            f"Recipient Address: {instance.recipient_address}\n"
            f"Status: {instance.status}\n"
            f"Timestamp: {format_timestamp(instance.timestamp)}\n"
        )
        recipient_list = ['orbitstockindex@gmail.com']
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
