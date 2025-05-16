

from django.urls import include, re_path, path


from .views import *
from . import views

app_name = 'accounts'

urlpatterns = [

    path('profile/', views.view_profile, name='view_profile'),
    re_path(r'^user/invest-now/$', invest_now, name='invest_now'),
    re_path(r'^planb/invest-now/$', plan_b, name='plan_b'),
    re_path(r'^plan_c/invest-now/$', plan_c, name='plan_c'),
    re_path(r'^plan_d/invest-now/$', plan_d, name='plan_d'),
    re_path(r'^plan_e/invest-now/$', plan_e, name='plan_e'),
    re_path(r'^plan_f/invest-now/$', plan_f, name='plan_f'),
    re_path(r'^schema$', schema, name='schema'),
    re_path(r'^investment_history$', investment_history, name='investment_history'),
    re_path(r'^login/$', login_view, name='login'),
    re_path(r'^register/$', register_view, name='register'),
    re_path(r'^logout/$', logout_view, name='logout'),
    re_path(r'^select_user/$', select_user, name='select_user'),
    re_path(r'^login_history/$', login_history, name='login_history'),
    re_path(r'^change-password/$', change_password_view, name='change_password'),
    re_path(r'^login_con$', login_con, name='login_con'),
    re_path(r'^useremail$', useremail, name='useremail'),
    re_path(r'^kyc_verification$', kyc_verification, name='kyc_verification'),
    re_path(r'^edit-profile/$', edit_profile, name='edit_profile'),
]
