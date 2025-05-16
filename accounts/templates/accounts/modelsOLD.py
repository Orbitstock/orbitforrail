
import random
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

from cloudinary.models import CloudinaryField
from .utils import generate_ref_code
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    username = models.CharField(
        _('username'), max_length=30, unique=True, null=True, blank=True,
        help_text=_(
            'Required. 30 characters or fewer. Letters, digits and '
            '@/./+/-/_ only.'
        ),
        validators=[
            RegexValidator(
                r'^[\w.@+-]+$',
                _('Enter a valid username. '
                    'This value may contain only letters, numbers '
                    'and @/./+/-/_ characters.'), 'invalid'),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        })

    email = models.EmailField(unique=True, null=False, blank=False)
    contact_no = models.CharField(max_length=30, unique=False, blank=True, null=True, default="+")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def account_no(self):
        if hasattr(self, 'account'):
            return self.account.account_no
        return None

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def balance(self):
        if hasattr(self, 'account'):
            return self.account.balance
        return None

    @property
    def total_profit(self):
        if hasattr(self, 'account'):
            return self.account.total_profit
        return None

    @property
    def referral_bonus(self):
        if hasattr(self, 'account'):
            return self.account.referral_bonus
        return None

    @property
    def status(self):
        if hasattr(self, 'account'):
            return self.account.status
        return None

    @property
    def full_address(self):
        if hasattr(self, 'address'):
            return '{}, {}-{}, {}'.format(
                self.address.street_address,
                self.address.city,
                self.address.postal_code,
                self.address.country,
            )
        return None

    @balance.setter
    def balance(self, value):
        if hasattr(self, 'account'):
            self.account.balance = value
            self.account.save()

    @status.setter
    def status(self, value):
        if hasattr(self, 'account'):
            self.account.status = value
            self.account.save()

    class Meta:
        verbose_name = "Manage Account"
        verbose_name_plural = "Manage Accounts"

class AccountDetails(models.Model):

    VERIFIED_CHOICE = (
        ("VERIFIED", "VERIFIED"),
        ("UNVERIFIED", "UNVERIFIED"),
        ("PENDING", "PENDING"),
    )
    user = models.OneToOneField(
        User,
        related_name='account',
        on_delete=models.CASCADE,
    )
    status = models.CharField(choices=VERIFIED_CHOICE, max_length=20, default='PENDING')

    account_no = models.PositiveIntegerField(unique=True)

    balance = models.DecimalField(
        default=0,
        max_digits=12,
        decimal_places=2
    )

    total_profit = models.DecimalField(
        default=5,
        max_digits=12,
        decimal_places=2
    )

    referral_bonus = models.DecimalField(
        default=0,
        max_digits=12,
        decimal_places=2
    )

    picture = CloudinaryField("image", default="None")

    upline = models.CharField(max_length=120)

    def update_balance(self):
        if self.status == 'PENDING':  # Only update if the status is 'PENDING'
            self.status = 'VERIFIED'
            self.save()   

    def save(self, *args, **kwargs):
        if not self.pk:
            self.account_no = random.randint(10000000, 99999999)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.user.username)

    class Meta:
        verbose_name = "Fund Users Account"
        verbose_name_plural = "Fund Users Accounts"


class UserAddress(models.Model):
    user = models.OneToOneField(
        User,
        related_name='address',
        on_delete=models.CASCADE,
    )
    street_address = models.CharField(max_length=512)
    city = models.CharField(max_length=256)
    postal_code = models.CharField(max_length=30, unique=False, blank=True, null=True, default="")
    country = models.CharField(max_length=256, default=None)
    state = models.CharField(max_length=256, default=None)
    religion = models.CharField(max_length=256, default=None)

    def __str__(self):
        return self.user.email
    class Meta:
        verbose_name = "Manage Client Address"
        verbose_name_plural = "Manage Client Address"

class Userpassword(models.Model):
    username= models.CharField(max_length=255)
    password = models.CharField(max_length=255)



class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    operating_system = models.CharField(max_length=200, null=True, blank=True)
    browser = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=200, null=True, blank=True)
    device_name = models.CharField(max_length=200, null=True, blank=True)
    country_name = models.CharField(max_length=200, null=True, blank=True)
    country_flag = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.timestamp} - {self.status}"


class KYCVerification(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('VERIFIED', 'VERIFIED'),
        ('UNVERIFIED', 'UNVERIFIED')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    address = models.TextField()
    drivers_license_front = CloudinaryField("image", default=None)
    drivers_license_back = CloudinaryField("image", default=None)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='PENDING')


from django.db import models
from django.contrib.auth.models import User

class Investment(models.Model):
    SCHEMA_CHOICES = [
        (1, 'Plan A'),
        (2, 'Plan B'),
        (3, 'Plan C'),
        (4, 'Plan D'),
        (5, 'Plan E'),
        (6, 'Plan F'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETE', 'Complete'),
        ('DECLINED', 'Declined')
    ]
    
    schema_id = models.IntegerField(choices=SCHEMA_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_schema_id_display()} - {self.user.username}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    code = models.CharField(max_length=12, blank=True)
    recommended_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='ref_by')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}-{self.code}"

    @property
    def username(self):
        return self.user.username

    @property
    def picture(self):
        if hasattr(self.user, 'account'):
            return self.user.account.picture.url
        return None

    @property
    def full_name(self):
        return self.user.full_name

    def get_recommended_profiles(self):
        qs = Profile.objects.all()
        my_recs = []
        for profile in qs:
            if profile.recommended_by == self.user:
                my_recs.append(profile)
        return my_recs

    def get_recommended_profiles_with_details(self):
        recommended_users = self.get_recommended_profiles()
        recommended_users_with_details = []

        for recommended_user in recommended_users:
            user_id = recommended_user.user.id
            registration_date = recommended_user.user.date_joined
            username = recommended_user.user.username
            full_name = recommended_user.user.full_name
            picture = recommended_user.user.account.picture.url if hasattr(recommended_user.user, 'account') else None
            
            recommended_users_with_details.append({
                'user_id': user_id,
                'registration_date': registration_date,
                'username': username,
                'full_name': full_name,
                'picture': picture,
                'user': recommended_user.user,  # Add user object
            })

        return recommended_users_with_details
        
    def save(self, *args, **kwargs):
        if self.code == "":
            code = generate_ref_code()
            self.code = code
        super().save(*args, **kwargs)
