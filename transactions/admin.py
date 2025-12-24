
from django.contrib import admin

from .models import *
# Register your models here.
from django.utils.html import format_html

from django.db import models
import uuid
from bankingsystem.admin_actions import export_as_csv

@admin.register(NewEvent)
class NewEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'reward_amount', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'topic')

@admin.register(NewEventApplication)
class NewEventApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'reward_status', 'application_date')
    list_filter = ('status', 'reward_status')
    search_fields = ('user__username', 'event__name')

@admin.register(RecentWinner)
class RecentWinnerAdmin(admin.ModelAdmin):
    list_display = ('name',)



class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'status', 'amount', 'recipient_account', 'date', 'client_email')
    list_filter = ('status', )
    search_fields = ('user__email', 'user__username')
    
    def client_name(self, obj):
        return obj.user.get_full_name()
    client_name.short_description = 'Client Name'
    
    def client_email(self, obj):
        return obj.user.email
    client_email.short_description = 'Client Email'
    
    def recipient_account(self, obj):
        return obj.target
    recipient_account.short_description = 'Recipient Account'
    

    
admin.site.register(Withdrawal, WithdrawalAdmin)

@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = ('method', 'name_tag')
    search_fields = ('method',)
    list_filter = ('name_tag',)

    
@admin.register(TransactionHistory)
class TransactionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'status', 'timestamp')
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = ('user__username', 'transaction_type', 'status')
    date_hierarchy = 'timestamp'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_email', 'subject', 'contact_date')
    list_filter = ('contact_date',)
    search_fields = ('name', 'user__username', 'user__email')
    date_hierarchy = 'contact_date'
    ordering = ('-contact_date',)
    list_per_page = 20

    def user_email(self, obj):
        return obj.user.email if obj.user else None
    user_email.short_description = 'User Email'


class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')
    list_filter = ('name', 'email')

admin.site.register(CONTACT_US, ContactUsAdmin)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'date']
    list_filter = ['status', 'date']




class CryptoWITHDRAWAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_method', 'amount', 'status', 'date')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__username', 'user__email')



admin.site.register(CryptoWITHDRAW, CryptoWITHDRAWAdmin)


from django.contrib import admin
from django import forms
from .models import CRYPWALLETS


@admin.register(CRYPWALLETS)
class CRYPWALLETSAdmin(admin.ModelAdmin):
    list_display = ('bitcoin', 'ethereum', 'usdt_trc20', 'xrp')
    search_fields = ('bitcoin', 'ethereum', 'usdt_trc20', 'xrp')
    list_filter = ('bitcoin', 'ethereum')

    # Optional field grouping
    fieldsets = (
        ('Bitcoin Wallet', {
            'fields': ('bitcoin', 'bitcoin_qr_code'),
        }),
        ('Ethereum Wallet', {
            'fields': ('ethereum', 'ethereum_qr_code'),
        }),
        ('USDT TRC20 Wallet', {
            'fields': ('usdt_trc20', 'usdt_trc20_qr_code'),
        }),
        ('XRP Wallet', {
            'fields': ('xrp', 'xrp_qr_code'),
        }),
    )

    # ✅ THIS is the hard enforcement that strips all unwanted fields
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        allowed_fields = {
            'bitcoin', 'bitcoin_qr_code',
            'ethereum', 'ethereum_qr_code',
            'usdt_trc20', 'usdt_trc20_qr_code',
            'xrp', 'xrp_qr_code'
        }

        # Remove all other fields from the form
        for field_name in list(form.base_fields.keys()):
            if field_name not in allowed_fields:
                form.base_fields.pop(field_name)
        return form


admin.site.register(Payment, PaymentAdmin)
admin.site.add_action(export_as_csv, name='export_selected')

