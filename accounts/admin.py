from django.contrib import admin

from .models import *
from .forms import *

from bankingsystem.admin_actions import export_as_csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = ['ban_users', 'unban_users']
    list_display = BaseUserAdmin.list_display + ('is_banned', 'is_active', 'email', 'username', 'full_name', 'contact_no', 'balance', 'account_status')
    list_filter = BaseUserAdmin.list_filter + ('is_banned', 'is_active')

    def ban_users(self, request, queryset):
        queryset.update(is_banned=True, is_active=False)
    ban_users.short_description = "Ban selected users"

    def unban_users(self, request, queryset):
        queryset.update(is_banned=False, is_active=True, ban_reason=None)
    unban_users.short_description = "Unban selected users"

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Client Name'

    def account_status(self, obj):
        if obj.account:
            return 'Active'
        return 'Inactive'
    account_status.short_description = 'Account Status'





class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'code')
    search_fields = ('user__username', 'code')
    list_select_related = ('user',)



admin.site.register(Profile, ProfileAdmin)



@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'full_name', 'address')


class UserpasswordAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name')  # Include the custom method in list_display
    list_filter = ('username',)
    search_fields = ('username',)
    ordering = ('username',)

    # ... other admin customization ...

    def get_full_name(self, obj):
        return f"{obj.username}"  # You can customize this to generate the full name
    get_full_name.short_description = 'Full Name'  # Set the column header in the admin list view

admin.site.register(Userpassword, UserpasswordAdmin)


@admin.register(AccountDetails)
class AccountDetailsAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'username', 'account_no', 'balance']
    search_fields = ['user__username', 'account_no']

    def full_name(self, obj):
        return obj.user.get_full_name()

    def username(self, obj):
        return obj.user.username

    full_name.short_description = 'Full Name'
    username.short_description = 'Username'


"""
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'timestamp', 'status')  # Include the fields you want to display
    list_filter = ('user',)  # Add user to list_filter if you want to filter by user
    search_fields = ('user__username', 'user__first_name', 'user__last_name')  # Add search fields for user
    ordering = ('user', 'timestamp')

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user.get_full_name() else 'N/A'
    get_full_name.short_description = 'Full Name'

admin.site.register(LoginHistory, LoginHistoryAdmin)
"""




@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    form = InvestmentAdminForm
    list_display = ('user', 'get_schema_display', 'status', 'amount', 'created_at')

    def get_schema_display(self, obj):
        schema_names = {
            1: 'Silver Plan',
            2: 'Bronze Plan',
            3: 'Gold Plan',
            4: 'Diamond Plan',
            5: 'Compounding Advanced Package',
            6: 'Fortune Advanced Package',
        }
        return schema_names.get(obj.schema_id, 'Unknown Plan')
    get_schema_display.short_description = 'Schema'

admin.site.add_action(export_as_csv, name='export_selected')
