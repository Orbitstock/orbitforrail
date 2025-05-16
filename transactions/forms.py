
from django import forms

from django import forms
from .models import *
from datetime import date



class ContactForm(forms.ModelForm):
    class Meta:
        model = CONTACT_US
        fields = ['name', 'email', 'message']


class SupportForm(forms.ModelForm):
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

    tickets = forms.ChoiceField(choices=SUPPORT_TICKETS, widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select Department'}))

    class Meta:
        model = SUPPORT
        fields = ['tickets', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control'}),
        }


class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = LoanRequest
        fields = ['credit_facility', 'payment_tenure', 'reason', 'amount']
        widgets = {
            'credit_facility': forms.Select(attrs={'class': 'form-control'}),
            'payment_tenure': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        


class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = Withdrawal
        fields = ["amount", "target", "target_email", "note"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(WithdrawalForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if self.user.account.balance < amount:
            raise forms.ValidationError(
                'You Can Not Withdraw More Than Your Balance.'
            )

        return amount

    def clean_target(self):
        target = self.cleaned_data['target']

        

        return target


    def clean_target_email(self):
        target = self.cleaned_data['target_email']

        

        return target

    def clean_note(self):
        note = self.cleaned_data['note']

        

        return note





class PaymentForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('crypto', 'Cryptocurrency'),
        ('giftcard', 'Gift Card'),
        ('bank', 'Bank Transfer'),
    ]

    payment = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}),
        required=True
    )

    # Cryptocurrency fields
    crypto_method = forms.ChoiceField(
        choices=[('BITCOIN', 'Bitcoin'), ('ETHEREUM', 'Ethereum'), ('USDT_TRC20', 'Usdt Trc20'), ('XRP', 'Xrp')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'crypto-method'})
    )

    # Gift Card fields
    giftcard_type = forms.ChoiceField(
        choices=[('Select Giftcard', 'Select Giftcard'),('APPLE', 'Apple'), ('GOOGLE', 'Google'), ('ITUNES', 'iTunes'), ('AMAZON', 'Amazon')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'giftcard-type'})
    )
    giftcard_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Gift Card Code'})
    )

    # Bank Transfer fields
    bank_transfer = forms.ModelChoiceField(
        queryset=BankTransfer.objects.all(),
        required=False,
        empty_label="Select Bank Transfer Method",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'bank-method'})
    )

    amount = forms.DecimalField(
        min_value=10.00,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter Amount'})
    )
    proof_of_pay = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'id': 'proof-of-pay-input',
            'onchange': 'previewImage(event)',  # JavaScript function to preview image
        })
    )
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment', 'crypto_method', 'giftcard_type', 'giftcard_code', 'bank_transfer', 'proof_of_pay']


    class Meta:
        model = Payment
        fields = ['amount', 'payment', 'crypto_method', 'giftcard_type', 'giftcard_code', 'bank_transfer']

    def clean(self):
        cleaned_data = super().clean()
        payment = cleaned_data.get('payment')

        if payment == 'crypto':
            if not cleaned_data.get('crypto_method'):
                raise forms.ValidationError("Please select a cryptocurrency type.")
        elif payment == 'giftcard':
            if not cleaned_data.get('giftcard_type') or not cleaned_data.get('giftcard_code'):
                raise forms.ValidationError("Both gift card type and code are required for Gift Card payments.")
        elif payment == 'bank':
            if not cleaned_data.get('bank_transfer'):
                raise forms.ValidationError("Please select a bank transfer method.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        payment = self.cleaned_data.get('payment')

        if payment == 'crypto':
            instance.payment_method = self.cleaned_data.get('crypto_method')
        elif payment == 'giftcard':
            instance.payment_method = 'GIFTCARD'
            instance.giftcard_type = self.cleaned_data.get('giftcard_type')
            instance.giftcard_code = self.cleaned_data.get('giftcard_code')
        elif payment == 'bank':
            instance.payment_method = 'BANK_TRANSFER'
            instance.bank_transfer = self.cleaned_data.get('bank_transfer')

        if commit:
            instance.save()
        return instance



class CryptoWITHDRAWForm(forms.ModelForm):
    class Meta:
        model = CryptoWITHDRAW
        fields = ['payment_method', 'amount', 'recipient_address']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'recipient_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def has_error(self, field_name):
        return self[field_name].errors

    def get_error(self, field_name):
        return self[field_name].errors.as_text()

