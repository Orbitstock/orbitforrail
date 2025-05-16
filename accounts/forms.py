
import datetime
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import *
from django.contrib.auth.forms import UserChangeForm

class InvestmentAdminForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['schema_id'].widget = forms.Select(choices=[
            (1, 'Silver Plan'),
            (2, 'Bronze Plan'),
            (3, 'Gold Plan'),
            (4, 'Diamond Plan'),
            (5, 'Compounding Advanced Package'),
            (6, 'Fortune Advanced Package'),
        ])

class KYCVerificationForm(forms.ModelForm):
    class Meta:
        model = KYCVerification
        fields = ['full_name', 'address', 'drivers_license_front', 'drivers_license_back']

    full_name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Full Name'}
        )
    )

    address = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Address'}
        )
    )


class InvestmentForm(forms.ModelForm):
    PLAN_CHOICES = [
        ('', 'Select a Plan'),  # Add an empty option
        (1, 'Silver Plan'),
        (2, 'Bronze Plan'),
        (3, 'Gold Plan'),
        (4, 'Diamond Plan'),
        (5, 'Compounding Advanced Package'),
        (6, 'Fortune Advanced Package'),
    ]

    schema_id = forms.ChoiceField(choices=PLAN_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = Investment
        fields = ['schema_id', 'amount']

    def clean_amount(self):
        schema_id = int(self.cleaned_data['schema_id'])
        amount = self.cleaned_data['amount']

        # Define the minimum and maximum investment amounts for each plan
        min_investment_amounts = {
            1: 500,     # Silver Plan
            2: 1000,    # Bronze Plan
            3: 5000,    # Gold Plan
            4: 30000,   # Diamond Plan
            5: 100000,    # Compounding Advanced Package
            6: 500000,  # Fortune Advanced Package
        }
        
        max_investment_amounts = {
            1: 999,      # Silver Plan
            2: 4999,     # Bronze Plan
            3: 29999,    # Gold Plan
            4: 99999,    # Diamond Plan
            5: None,     # Compounding Advanced Package
            6: None,     # Fortune Advanced Package
        }

        min_amount = min_investment_amounts.get(schema_id, 0)
        max_amount = max_investment_amounts.get(schema_id)

        if amount < min_amount:
            raise forms.ValidationError('Minimum investment amount not met for the selected plan.')

        if max_amount and amount > max_amount:
            raise forms.ValidationError('Maximum investment amount exceeded for the selected plan.')

        return amount



class PasswordInputWithToggle(forms.PasswordInput):
    template_name = 'accounts/password_input_with_toggle.html'

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]
        labels = {
            "username": "Username",
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
            "password1": "Password",
            "password2": "Confirm Password",
        }
        widgets = {
            "password1": PasswordInputWithToggle(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}),
            "password2": PasswordInputWithToggle(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
            "username": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            "first_name": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            "last_name": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            "email": forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }


class AccountDetailsForm(forms.ModelForm):
    class Meta:
        model = AccountDetails
        fields = ['picture']  # Removed 'upline' from the fields list
        labels = {'picture': 'Picture'}
        widgets = {
            'picture': forms.ClearableFileInput(),  # Removed 'upline' widget
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Removed the logic for setting 'upline' field in __init__ method


class UserProfileEditForm(UserChangeForm):
    password = None  # Remove the password field from the form
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'contact_no']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AccountDetailsEditForm(forms.ModelForm):
    class Meta:
        model = AccountDetails
        fields = ['picture']
        widgets = {
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your old password was entered incorrectly. Please enter it again.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return cleaned_data





class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your username',
                'required': True,
            }
        )
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your password',
                'required': True,
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['autocomplete'] = 'off'

