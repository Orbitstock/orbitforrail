
from django.urls import include, re_path, path

from .views import *

app_name = 'transactions'

urlpatterns = [
    # re_path(r'^$', home_view, name='home'),
    re_path(r'^create/$', payment_create, name='payment_create'),
    re_path(r'^success/$', payment_success, name='payment_success'),
    re_path(r'^withdrawal/$', withdrawal_view, name='withdrawal'),

    re_path(r'^recent_payments/$', recent_payments, name='recent_payments'),
    re_path(r'^Transaction_processing/$', login_con, name='login_con'),
    re_path(r'^Transaction_connecting/$', admin_not, name='admin_not'),
    re_path(r'^terms/$', terms, name='terms'),
    re_path(r'^summary/$', transaction_history, name='history'),
    re_path(r'^history/$', historia, name='summary'),
    re_path(r'^wallets/$', wallet, name='wallet'),
    re_path(r'^summary/export/$', transaction_history, name='history_pdf_export'),
    re_path(r'^create_withdrawal/$', create_withdrawal, name='create_withdrawal'),
    re_path(r'^crypto_success/$', crypto_success, name='crypto_success'),
    re_path(r'^referral/$', referral, name='referral'),
    re_path(r'^download-transaction-pdf/$', download_transaction_pdf, name='download_transaction_pdf'),

]
