import uuid

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils import timezone
from cloudinary.models import CloudinaryField
from datetime import datetime
import random
import string
from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import transaction

User = settings.AUTH_USER_MODEL




class NewEvent(models.Model):
    name = models.CharField(max_length=20, blank=True, null=True)
    image = CloudinaryField('notification_images/', default="default_notification_image.png")
    topic = models.CharField(max_length=20, blank=True, null=True)
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = RichTextUploadingField(blank=True, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    recent_winners = models.ManyToManyField('RecentWinner', related_name='winners', blank=True)
    is_active = models.BooleanField(default=True, help_text="Manually toggle to open or close the event.")

    class Meta:
        verbose_name = 'z - NewEvent'
        verbose_name_plural = 'z - NewEvents'

    def __str__(self):
        return f"{self.name.capitalize()} NewEvent - {self.id}"

    def is_active_event(self):
        """
        Check if the event is still active based on time and status.
        Automatically deactivate the event if the current time exceeds the end date.
        """
        if self.start_date <= timezone.now() <= self.end_date and self.is_active:
            return True
        self.is_active = False
        self.save()
        return False

    def toggle_active_status(self):
        """
        Toggle the 'is_active' field and apply manual deactivation logic.
        """
        self.is_active = not self.is_active
        self.save()
        
        # Handle deactivation: Automatically reject associated applications
        if not self.is_active:
            self.applications.update(status='rejected')  # Disable all applications for the event
        else:
            # Optionally, add logic to re-enable certain behaviors when reactivating
            pass

    def save(self, *args, **kwargs):
        """
        Ensure that an event cannot be saved as active if it has expired.
        """
        if self.is_active and timezone.now() > self.end_date:
            raise ValueError("Cannot activate an event that has already expired.")
        super().save(*args, **kwargs)




class NewEventApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    REWARD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('collected', 'Collected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_applications')
    event = models.ForeignKey(NewEvent, on_delete=models.CASCADE, related_name='applications')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reward_status = models.CharField(max_length=20, choices=REWARD_STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = 'z -Event Application'
        verbose_name_plural = 'z -Event Applications'

    def __str__(self):
        return f"{self.user.username} - {self.event.name} Application"

    def save(self, *args, **kwargs):
        # Prevent saving to an inactive event
        if not self.event.is_active:
            raise ValueError(f"Cannot apply to an inactive event: {self.event.name}.")

        # Handle changes in reward status
        if self.pk:  # Check if the instance exists in the database
            original = NewEventApplication.objects.get(pk=self.pk)
            if original.reward_status != 'collected' and self.reward_status == 'collected':
                self.add_reward_to_balance()
        
        super().save(*args, **kwargs)

    def add_reward_to_balance(self):
        """Add the reward amount to the user's balance."""
        with transaction.atomic():
            self.user.balance += self.event.reward_amount
            self.user.save()

# Signal to handle notifications
@receiver(post_save, sender=NewEventApplication)
def handle_application_changes(sender, instance, created, **kwargs):
    """Automatically create notification on application submission."""
    if created:
        # Notify the user about their application submission
        Notification.objects.create(
            name=f"Application Submitted: {instance.event.name}",
            user=instance.user,
            subject="Your application has been received",
            message=f"You have successfully applied for the event '{instance.event.name}'. Status: Submitted.",
            contact_date=now()
        )


class RecentWinner(models.Model):
    name = models.CharField(max_length=255, verbose_name='Recent Winners')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'z - WINNER'
        verbose_name_plural = 'z - WINNERs'





class TransactionHistory(models.Model):
    TRANSACTION_TYPES = [
        ('WITHDRAWAL', 'Withdrawal'),
        ('LOAN_REQUEST', 'Loan Request'),
        ('DEPOSIT', 'Deposit'),
        ('CRYPTO_WITHDRAW', 'Crypto Withdrawal'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('DECLINED', 'Declined'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_history')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now, editable=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    target = models.CharField(max_length=200, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    transaction_id = models.CharField(max_length=50, unique=True, editable=False)
    total_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_crypto_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        super().save(*args, **kwargs)

    def generate_transaction_id(self):
        unique_id = uuid.uuid4().hex[:6].upper()
        return f"TXN-{self.user.id}-{unique_id}"

    def update_totals(self):
        old_status = TransactionHistory.objects.get(pk=self.pk).status if self.pk else None
        if self.status in ['COMPLETED', 'COMPLETE']:
            if self.transaction_type == 'WITHDRAWAL':
                self.total_withdrawal = F('total_withdrawal') + self.amount
            elif self.transaction_type == 'DEPOSIT':
                self.total_deposit = F('total_deposit') + self.amount
            elif self.transaction_type == 'CRYPTO_WITHDRAW':
                self.total_crypto_withdrawal = F('total_crypto_withdrawal') + self.amount
        elif self.status == 'CANCELLED' and old_status in ['COMPLETED', 'COMPLETE']:
            if self.transaction_type == 'WITHDRAWAL':
                self.total_withdrawal = F('total_withdrawal') - self.amount
            elif self.transaction_type == 'DEPOSIT':
                self.total_deposit = F('total_deposit') - self.amount
            elif self.transaction_type == 'CRYPTO_WITHDRAW':
                self.total_crypto_withdrawal = F('total_crypto_withdrawal') - self.amount
        self.save(update_fields=['total_withdrawal', 'total_deposit', 'total_crypto_withdrawal'])

    def update_status(self):
        if self.content_object:
            old_status = self.status
            self.status = self.content_object.status
            if old_status != self.status:
                self.save()
                if self.status in ['COMPLETED', 'COMPLETE', 'CANCELLED']:
                    self.update_totals()

    def get_related_status(self):
        if self.content_object:
            return self.content_object.status
        return None

    def get_status_display(self):
        status = self.get_related_status()
        if status:
            if self.content_type.model == 'withdrawal':
                return dict(Withdrawal.STATUS_CHOICES).get(status, status)
            elif self.content_type.model in ['payment', 'cryptowithdraw']:
                return dict(Payment.STATUS_CHOICES).get(status, status)
        return self.status

    def __str__(self):
        return f"{self.transaction_id}: {self.user.username} - {self.transaction_type} - {self.amount} - {self.status}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Transaction Histories"

class Withdrawal(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('DECLINED', 'Declined'),
    )

    user = models.ForeignKey(User, related_name='withdrawals', on_delete=models.CASCADE)
    target = models.CharField(max_length=200)
    target_email = models.EmailField()
    note = models.TextField(default='none')
    amount = models.DecimalField(decimal_places=2, max_digits=12, validators=[MinValueValidator(Decimal('10.00'))])
    timestamp = models.DateTimeField(default=timezone.now, editable=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date = models.DateField(auto_now=True)

    def __str__(self):
        return str(self.user)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.create_transaction_history()
        else:
            self.update_transaction_history()

    def create_transaction_history(self):
        TransactionHistory.objects.create(
            user=self.user,
            transaction_type='WITHDRAWAL',
            amount=self.amount,
            status=self.status,
            content_object=self
        )

    def update_transaction_history(self):
        transaction_history = TransactionHistory.objects.get(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        )
        transaction_history.update_status()
        if self.status in ['COMPLETED', 'COMPLETE']:
            transaction_history.update_totals()

    class Meta:
        verbose_name = "3-Transfer"
        verbose_name_plural = "3- Transfers"

class Payment(models.Model):
    PAYMENT_CHOICES = [
        ('BITCOIN', 'Bitcoin'),
        ('ETHEREUM', 'Ethereum'),
        ('USDT_TRC20', 'USDT TRC20'),
        ('USDT_ERC20', 'USDT ERC20'),
        ('XRP', 'XRP'),
        ('GIFTCARD', 'Giftcard'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]

    GIFT_CARD_CHOICES = [
        ('Select Giftcard', 'Select Giftcard'),
        ('APPLE', 'Apple'),
        ('GOOGLE', 'Google'),
        ('ITUNES', 'iTunes'),
        ('AMAZON', 'Amazon'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETE', 'Complete'),
        ('CANCELLED', 'Cancelled'),
        ('DECLINED', 'Declined')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(choices=PAYMENT_CHOICES, max_length=15)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    proof_of_pay = CloudinaryField("image", default=None, blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='PENDING')
    date = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(default=timezone.now, editable=True)

    # Additional Fields for Giftcard and Bank Transfer
    giftcard_type = models.CharField(choices=GIFT_CARD_CHOICES, max_length=20, blank=True, null=True)
    giftcard_code = models.CharField(max_length=255, blank=True, null=True)
    bank_transfer = models.ForeignKey('BankTransfer', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        payment_info = f"Payment ID: {self.id} | User: {self.user} | Amount: {self.amount} | Date: {self.date.strftime('%Y-%m-%d %H:%M:%S')} | "
        if self.payment_method == 'GIFTCARD':
            return payment_info + f"Gift Card: {self.giftcard_type} | Code: {self.giftcard_code} |"
        elif self.payment_method == 'BANK_TRANSFER':
            # Check if the bank_transfer instance has a custom method name
            if self.bank_transfer.custom_method_name:
                return payment_info + f"Bank Transfer: {self.bank_transfer.custom_method_name} | Name Tag: {self.bank_transfer.name_tag} |"
            else:
                return payment_info + f"Bank Transfer: {self.bank_transfer.get_method_display()} | Name Tag: {self.bank_transfer.name_tag} |"
        return payment_info + f"Payment Method: {self.payment_method} |"

    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
            self.create_transaction_history()
        else:
            old_status = Payment.objects.get(pk=self.pk).status
            super().save(*args, **kwargs)
            if old_status != self.status:
                if self.status == 'COMPLETE':
                    self.update_balance(self.amount)
                elif self.status == 'CANCELLED' and old_status == 'COMPLETE':
                    self.update_balance(-self.amount)
        self.update_transaction_history()

    def create_transaction_history(self):
        TransactionHistory.objects.create(
            user=self.user,
            transaction_type='DEPOSIT',
            amount=self.amount,
            status=self.status,
            content_object=self
        )

    def update_transaction_history(self):
        transaction_history = TransactionHistory.objects.get(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        )
        transaction_history.status = self.status
        transaction_history.save()

    def update_balance(self, amount):
        self.user.balance += amount
        self.user.save()

    class Meta:
        verbose_name = "1- Manage Deposit/Payment"
        verbose_name_plural = "1- Manage Deposit/Payment"

class BankTransfer(models.Model):
    PAYMENT_METHODS = [
        ('CASH_APP', 'Cash App'),
        ('PAYPAL', 'PayPal'),
        ('ZELLE', 'Zelle'),
    ]
    
    # Keep predefined payment methods
    method = models.CharField(choices=PAYMENT_METHODS, max_length=10, blank=True, null=True)

    # Dynamic payment method option added by the admin (replaces 'CUSTOM')
    custom_method_name = models.CharField(max_length=50, blank=True, null=True, help_text="Leave blank if using a predefined method")

    name_tag = models.CharField(max_length=100, help_text="Cash App Tag or PayPal/Zelle identifier")
    qr_code_image = CloudinaryField("image", default=None, blank=True, null=True)
    bank_image = CloudinaryField("image", default=None, blank=True, null=True)

    def __str__(self):
        # Use the dynamic custom method name if it's provided
        if self.custom_method_name:
            return f"{self.custom_method_name} - {self.name_tag}"
        # Otherwise, display the predefined method
        return f"{self.get_method_display()} - {self.name_tag}"

    class Meta:
        verbose_name = "5- Aza Detail"
        verbose_name_plural = "5-Aza Details"

class CRYPWALLETS(models.Model):
    bitcoin = models.CharField(max_length=500, blank=True, null=True)
    bitcoin_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    ethereum = models.CharField(max_length=500, blank=True, null=True)
    ethereum_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    usdt_erc20 = models.CharField(max_length=500, blank=True, null=True)
    usdt_erc20_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    solana = models.CharField(max_length=500, blank=True, null=True)
    solana_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    usdt_trc20 = models.CharField(max_length=500, blank=True, null=True)
    usdt_trc20_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    xrp = models.CharField(max_length=500, blank=True, null=True)
    xrp_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    bnb = models.CharField(max_length=500, blank=True, null=True)
    bnb_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    litecoin = models.CharField(max_length=500, blank=True, null=True)
    litecoin_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    dogecoin = models.CharField(max_length=500, blank=True, null=True)
    dogecoin_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    shiba_inu = models.CharField(max_length=500, blank=True, null=True)
    shiba_inu_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    cardano = models.CharField(max_length=500, blank=True, null=True)
    cardano_qr_code = CloudinaryField("image", default=None,blank=True, null=True)

    class Meta:
        verbose_name = "4- WALLETS"
        verbose_name_plural = "4- WALLETS"

class CryptoWITHDRAW(models.Model):
    PAYMENT_CHOICES = [
        ('BITCOIN', 'Bitcoin'),
        ('ETHEREUM', 'Ethereum'),
        ('USDT_TRC20', 'USDT TRC20'),
        ('USDT_ERC20', 'USDT ERC20')
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETE', 'Complete'),
        ('CANCELLED', 'Cancelled'),
        ('DECLINED', 'Declined')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(choices=PAYMENT_CHOICES, max_length=10)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    recipient_address = models.CharField(max_length=512, default='')
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='PENDING')
    date = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(default=timezone.now, editable=True)

    def __str__(self):
        return f"{self.user} withdrew {self.amount} via {self.payment_method}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
            self.create_transaction_history()
        else:
            old_status = CryptoWITHDRAW.objects.get(pk=self.pk).status
            super().save(*args, **kwargs)
            if old_status != self.status:
                if self.status == 'COMPLETE':
                    self.update_balance(-self.amount)
                elif self.status == 'CANCELLED' and old_status == 'COMPLETE':
                    self.update_balance(self.amount)
        self.update_transaction_history()

    def create_transaction_history(self):
        TransactionHistory.objects.create(
            user=self.user,
            transaction_type='CRYPTO_WITHDRAW',
            amount=self.amount,
            status=self.status,
            content_object=self
        )

    def update_transaction_history(self):
        transaction_history = TransactionHistory.objects.get(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        )
        transaction_history.status = self.status
        transaction_history.save()

    def update_balance(self, amount):
        self.user.balance += amount
        self.user.save()

    class Meta:
        verbose_name = "2- Crypto Withdrawal"
        verbose_name_plural = "2- Crypto Withdrawals"

class LoanRequest(models.Model):
    FACILITY = [
        ('Personal Home Loans', 'Personal Home Loans'),
        ('Joint Mortgage', 'Joint Mortgage'),
        ('Automobile Loans', 'Automobile Loans'),
        ('Salary loans', 'Salary loans'),
        ('Secured Overdraft', 'Secured Overdraft'),
        ('Contract Finance', 'Contract Finance'),
        ('Secured Term Loans', 'Secured Term Loans'),
        ('StartUp/Products Financing', 'StartUp/Products Financing'),
        ('Local Purchase Orders Finance', 'Local Purchase Orders Finance'),
        ('Operational Vehicles', 'Operational Vehicles'),
        ('Revenue Loans and Overdraft', 'Revenue Loans and Overdraft'),
        ('Retail TOD', 'Retail TOD'),
        ('Commercial Mortgage', 'Commercial Mortgage'),
        ('Office Equipment', 'Office Equipment'),
        ('Health Finance Product Guideline', 'Health Finance Product Guideline'),
        ('Health Finance', 'Health Finance')
    ]

    TENURE = [
        ('6 Months', '6 Months'),
        ('12 Months', '12 Months'),
        ('2 Years', '2 Years'),
        ('3 Years', '3 Years'),
        ('4 Years', '4 Years'),
        ('5 Years', '5 Years')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credit_facility = models.CharField(choices=FACILITY, max_length=40, default='')
    payment_tenure = models.CharField(choices=TENURE, max_length=40, default='')
    reason = models.TextField()
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email}: {self.amount} for {self.reason}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_transaction_history()

    def update_transaction_history(self):
        if self.status == 'completed':
            transaction_history = TransactionHistory.objects.create(
                user=self.user,
                transaction_type='LOAN_REQUEST',
                amount=self.amount,
                status=self.status,
                content_object=self
            )
            transaction_history.save()


class SUPPORT(models.Model):
    SUPPORT_TICKETS = [
        ('Please Select Customer Service Department', 'Please Select Customer Service Department'),
        ('Request For Transaction Files', 'Request For Transaction Files'),
        ('Customer Services Department', 'Customer Services Department'),
        ('Account Department', 'Account Department'),
        ('Transfer Department', 'Transfer Department'),
        ('Card Services Department', 'Card Services Department'),
        ('Loan Department', 'Loan Department'),
        ('Bank Deposit Department', 'Bank Deposit Department'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tickets = models.CharField(max_length=255, choices=SUPPORT_TICKETS)
    message = models.CharField(max_length=500)

    timestamp = models.DateTimeField(default=timezone.now, editable=True)


    class Meta:
        verbose_name = "SUPPORT"
        verbose_name_plural = "SUPPORTs"


class CONTACT_US(models.Model):
    name= models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()

    class Meta:
        verbose_name = "CONTACT US"
        verbose_name_plural = "CONTACT US"


class Notification(models.Model):    
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notify')
    image = CloudinaryField('notification_images/', default="https://res.cloudinary.com/dfkuixeji/image/upload/v1732216982/download_i49r46.jpg")
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    contact_date = models.DateTimeField(default=datetime.now, blank=True)
    read = models.BooleanField(default=False)  # New field to track read status

    def __str__(self):
        return self.name





from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Q
from django.utils import timezone
from django.template.loader import get_template
from django.conf import settings

from .models import *
from .forms import *
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib import colors
from xhtml2pdf import pisa
from io import BytesIO
from django.db.models import F

import os
from accounts.models import *
from accounts.models import Investment

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import NewEvent, NewEventApplication, Notification
from django.utils import timezone

@login_required
def available_events(request):
    # Get all active events
    current_events = NewEvent.objects.filter(
        is_active=True, 
        start_date__lte=timezone.now(), 
        end_date__gte=timezone.now()
    )
    
    # Get events the user has already applied to
    applied_event_ids = NewEventApplication.objects.filter(
        user=request.user
    ).values_list('event_id', flat=True)
    
    context = {
        'current_events': current_events,
        'applied_event_ids': applied_event_ids
    }
    return render(request, 'transactions/events/available_events.html', context)


@login_required
def user_event_applications(request):
    # Get all event applications for the current user
    user_applications = NewEventApplication.objects.filter(
        user=request.user
    ).order_by('-application_date')

    # Query all events and their winners
    events = NewEvent.objects.prefetch_related('recent_winners').all()
    
    winners_data = []
    for event in events:
        # Get all winners for this event
        event_winners = event.recent_winners.all()
        
        for winner in event_winners:
            winner_data = {
                'winner_name': winner.name,
                'event_id': event.id,
                'event_name': event.name,
                'event_topic': event.topic,
                'event_reward': event.reward_amount,
                'event_image': event.image.url if event.image else None,
                'event_description': event.description,
                'event_end_date': event.end_date,
            }
            winners_data.append(winner_data)
            print(f"Added winner: {winner_data}")
    
    # Sort by event end date (most recent first)
    winners_data.sort(key=lambda x: x['event_end_date'], reverse=True)

    context = {
        'user_applications': user_applications,
        'winners_data': winners_data
    }
    return render(request, 'transactions/events/user_event_applications.html', context)


@login_required  # You might want to remove this if it's public
def display_recent_winners(request):
    # Get all events with their associated winners
    events = NewEvent.objects.prefetch_related('recent_winners').all()
    
    winners_data = []
    for event in events:
        # Get all winners for this event
        event_winners = event.recent_winners.all()
        
        for winner in event_winners:
            winner_data = {
                'winner_name': winner.name,
                'event_id': event.id,
                'event_name': event.name,
                'event_topic': event.topic,
                'event_reward': event.reward_amount,
                'event_image': event.image.url if event.image else None,
                'event_description': event.description,
                'event_end_date': event.end_date,
            }
            winners_data.append(winner_data)
            print(f"Added winner: {winner_data}")
    
    # Sort by event end date (most recent first)
    winners_data.sort(key=lambda x: x['event_end_date'], reverse=True)
    
    context = {
        'winners_data': winners_data
    }
    
    return render(request, 'transactions/events/event_list.html', context)


@login_required
def apply_to_event(request, event_id):
    event = get_object_or_404(NewEvent, id=event_id)
    
    # Check if user has already applied
    existing_application = NewEventApplication.objects.filter(
        user=request.user, 
        event=event
    ).exists()
    
    if existing_application:
        messages.warning(request, "You have already applied to this event.")
        return redirect('transactions:available_events')  # Add namespace
    
    # Create new application
    NewEventApplication.objects.create(
        user=request.user, 
        event=event
    )
    
    # Create a notification for the new application
    Notification.objects.create(
        user=request.user,
        name=f"Application for {event.name}",
        subject="Event Application",
        message=f"You have applied to the event: {event.name}",
        image=event.image
    )
    
    messages.success(request, f"Successfully applied to {event.name}")
    return redirect('transactions:user_event_applications')  # Add namespace



def download_transaction_pdf(request):
    template = get_template('transactions/transaction_history_pdf.html')
    context = transaction_history(request)  # Reuse the context processor
    html = template.render(context)
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transaction_history.pdf"'
        return response
    
    return HttpResponse('Error generating PDF', status=400)

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            # Add a success message
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('core:home')  # Redirect to the home page after successful submission
    else:
        form = ContactForm()

    context = {
        'form': form,
    }

    return render(request, 'core/contact_us.html', context)


@login_required
def admin_not(request):

    payment = Withdrawal.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'transactions/admin_not.html', {'payment': payment})

@login_required
def login_con(request):
    return render(request, 'transactions/login_con.html')



def terms(request):
    return render(request, 'transactions/terms.html')


def historia(request):
    return render(request, 'transactions/history.html')


def wallet(request):
    wallets_instance = CRYPWALLETS.objects.first()

    return render(request, 'transactions/manage.html',{ 'wallets_instance': wallets_instance})



@login_required
def referral(request):
    profile = Profile.objects.get(user=request.user)
    my_recs = profile.get_recommended_profiles()

    return render(request, 'transactions/referral.html', {'my_recs':my_recs})

@login_required
def payment_create(request):
    bank_transfer_methods = BankTransfer.objects.all()  # Fetch all bank transfer objects
    wallets_instance = CRYPWALLETS.objects.first()  # Fetch crypto wallet addresses
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)  # Ensure form handles file uploads
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user  # Set the user who is making the payment
            payment.proof_of_pay = request.FILES.get('proof_of_pay')  # Save the uploaded file
            payment.save()
            
            # Handle wallet address for crypto payments
            if payment.payment_method in ['BITCOIN', 'ETHEREUM', 'USDT_TRC20', 'XRP']:
                crypto_wallet = {
                    'BITCOIN': wallets_instance.bitcoin,
                    'ETHEREUM': wallets_instance.ethereum,
                    'USDT_TRC20': wallets_instance.usdt_trc20,
                    'XRP': wallets_instance.xrp,
                }.get(payment.payment_method, '')
                return render(request, 'transactions/payment_success.html', {
                    'payment': payment,
                    'crypto_wallet': crypto_wallet,
                })
            return redirect('transactions:payment_success')
        else:
            # Handle invalid form and display errors
            error_messages = form.errors.as_json()  # Get form errors in JSON format
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")  # Display each error to the user
    else:
        form = PaymentForm()
    
    return render(request, 'transactions/payment_form.html', {
        'form': form,
        'bank_transfer_methods': bank_transfer_methods,
        'wallets_instance': wallets_instance,
    })




@login_required
def payment_success(request):
    payment = Payment.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'transactions/payment_success.html', {'payment': payment})



@login_required
def create_withdrawal(request):
    if request.method == 'POST':
        form = CryptoWITHDRAWForm(request.POST)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user

            # Check if the withdrawal amount exceeds the user's balance
            if withdrawal.amount > request.user.balance:
                form.add_error('amount', 'Insufficient balance.')

            if not form.errors:
                withdrawal.save()
                
                return redirect('transactions:crypto_success')  # Replace with your success URL
    else:
        form = CryptoWITHDRAWForm()
    
    return render(request, 'transactions/withdrawal_form.html', {'form': form})



@login_required
def crypto_success(request):
    payment = CryptoWITHDRAW.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'transactions/withdraw_success.html', {'payment': payment})



@login_required
def recent_payments(request):
    recent_payments = Payment.objects.order_by('-date', '-timestamp')[:10]
    context = {'recent_payments': recent_payments}
    return render(request, 'transactions/payment.html', context)



@login_required()
def withdrawal_view(request):
    form = WithdrawalForm(request.POST or None, user=request.user)
    if form.is_valid():
        withdrawal = form.save(commit=False)
        withdrawal.user = request.user
        withdrawal.save()
        messages.success(
            request, 
            f'Withdrawal Pending! ${withdrawal.amount} will be transferred to {form.cleaned_data["target_email"]} and should arrive within <strong>10 minutes to 1 business day</strong>. Thank you for banking with us!'
        )
        return redirect("confirm")
    context = {
        "title": "Withdraw",
        "form": form
    }
    return render(request, "transactions/form.html", context)

def transaction_history(request):
    if request.user.is_authenticated:
        user = request.user
        transactions = TransactionHistory.objects.filter(user=request.user).order_by('-timestamp')

        loan_request_history = LoanRequest.objects.filter(user=user).order_by('-requested_at')
        payment_history = Payment.objects.filter(user=user).order_by('-date')
        crypto_history = CryptoWITHDRAW.objects.filter(user=user).order_by('-date')
        withdrawal_history = Withdrawal.objects.filter(user=user).order_by('-date')  # Add this line
        context = {
            'transaction_history': transactions,
            'loan_request_history': loan_request_history,
            'payment_history': payment_history,
            'crypto_history': crypto_history,
            'withdrawal_history': withdrawal_history,  # Add this line
        }
        if 'export' in request.GET and request.GET['export'] == 'pdf':
            return generate_pdf(context)
        return context
    else:
        return {}


from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from io import BytesIO
import os
from django.conf import settings
from django.http import HttpResponse

def generate_pdf(context):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transaction_history.pdf"'
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    # Add a background color as an RGB tuple
    background_color = colors.Color(0.94902, 0.94902, 0.94902)  # Light gray
    elements.append(Table([[background_color]], colWidths=letter[0]))

    # Add your company logo or image
    image_path = os.path.join(os.path.abspath(os.path.join(settings.BASE_DIR, 'static')), 'dig73.png')  # Update with your logo path
    logo = Image(image_path, width=200, height=100)
    elements.append(logo)

    # Add a title
    title_style = ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    title_font = ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
    title = "Transaction History"
    elements.append(Table([[title]], style=[title_style, title_font]))

    # Add an empty line
    elements.append(Table([['']]))

    # Create and format the table header
    table_header = ["Transaction ID", "Type", "Scope", "Amount", "Date", "Time", "Description", "Status"]
    data = [table_header]

    # Add data rows
    def format_date_time(dt):
        if isinstance(dt, datetime):
            return dt.strftime('%d %b %Y'), dt.strftime('%I:%M %p')
        return '', ''

    for transaction in context['transaction_history']:
        transaction_date, transaction_time = format_date_time(transaction.timestamp)
        
        if transaction.transaction_type == 'DEPOSIT':
            transaction_type = "Deposit"
            scope = "Fund Account"
        elif transaction.transaction_type == 'CRYPTO_WITHDRAW':
            transaction_type = "Withdrawal"
            scope = "Crypto Network"
        elif transaction.transaction_type == 'WITHDRAWAL':
            transaction_type = "Transfer"
            scope = "Internal Network"
        else:
            transaction_type = transaction.get_transaction_type_display()
            scope = "Other"

        data.append([
            transaction.transaction_id,
            transaction_type,
            scope,
            f"${transaction.amount}",
            transaction_date,
            transaction_time,
            transaction.payment_method or "N/A",
            transaction.get_status_display()
        ])

    # Create and format the table
    table = Table(data)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.50588, 0.50588, 0.50588)),  # Dark gray
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.90980, 0.90980, 0.90980)),  # Light gray
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#808080')),
    ]
    table.setStyle(TableStyle(table_style))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response



