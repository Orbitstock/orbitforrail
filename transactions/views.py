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



