
# custom_context_processors.py

from accounts.models import Profile
from transactions.models import *
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.core.paginator import Paginator

def recommended_users(request):
    # Add your logic to fetch recommended users here
    if request.user.is_authenticated:
        user_profile = Profile.objects.get(user=request.user)
        my_recs = user_profile.get_recommended_profiles_with_details()
    else:
        my_recs = []

    return {'my_recs': my_recs}


# custom_context_processors.py


# custom_context_processors.py

from datetime import datetime
from django.templatetags.static import static

def notifications(request):
    if request.user.is_authenticated:
        user = request.user
        notifications = Notification.objects.filter(user=user).order_by('-contact_date')
        notification_count = notifications.count()
        
        if notification_count == 0:
            # Create a default welcome notification if none exist
            welcome_notification = Notification(
                name="Welcome!",
                user=user,
                image=static('images/GEG.png'),  # Use the static function to get the default image URL
                subject="Welcome to our platform",
                message="Thank you for joining us! We hope you have a great experience.",
                contact_date=datetime.now(),
                read=False
            )
            notifications = [welcome_notification] + list(notifications)
            notification_count += 1
    else:
        notifications = []
        notification_count = 0
    
    context = {
        'notifications': notifications,
        'notification_count': notification_count,
    }

    return context
# custom_context_processors.py
from django.core.paginator import Paginator
from django.db.models import Sum

def transaction_history(request):
    context = {
        'transaction_history': [],
        'transaction_paginator': None,
        'total_deposit': 0,
        'total_withdrawal': 0,
        'total_crypto_withdrawal': 0,
        'deposit_count': 0,
        'crypto_withdraw_count': 0,
    }
    if request.user.is_authenticated:
        transactions = TransactionHistory.objects.filter(user=request.user).order_by('-timestamp')
        
        # Count deposit and crypto withdrawal transactions
        context['deposit_count'] = transactions.filter(transaction_type='DEPOSIT').count()
        context['crypto_withdraw_count'] = transactions.filter(transaction_type='CRYPTO_WITHDRAW').count()
        
        # Calculate total amounts for completed transactions
        completed_transactions = transactions.filter(status__in=['COMPLETED', 'COMPLETE'])
        context['total_deposit'] = completed_transactions.filter(transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_withdrawal'] = completed_transactions.filter(transaction_type='WITHDRAWAL').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_crypto_withdrawal'] = completed_transactions.filter(transaction_type='CRYPTO_WITHDRAW').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Pagination
        page_number = request.GET.get('transaction_page', 1)
        paginator = Paginator(transactions, 7)  # Show 7 transactions per page
        page_obj = paginator.get_page(page_number)
        context.update({
            'transaction_history': page_obj,
            'transaction_paginator': paginator,
        })
    return context

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return result.getvalue()
    return None