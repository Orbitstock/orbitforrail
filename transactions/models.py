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


User = settings.AUTH_USER_MODEL


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

"""@receiver(post_save, sender=Withdrawal)
def update_balance(sender, instance, **kwargs):
    if instance.status in ['COMPLETED', 'COMPLETE']:
        instance.user.balance -= instance.amount
    elif instance.status == 'CANCELLED':
        instance.user.balance += instance.amount
    instance.user.save()"""







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
    image = CloudinaryField('notification_images/', default="default_notification_image.png")
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    contact_date = models.DateTimeField(default=datetime.now, blank=True)
    read = models.BooleanField(default=False)  # New field to track read status

    def __str__(self):
        return self.name





