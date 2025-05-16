
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
import requests
from user_agents import parse
from django.contrib.messages import constants as messages_constants

from .forms import *
from .models import *



@login_required
def view_profile(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def kyc_verification(request):
    if request.method == 'POST':
        form = KYCVerificationForm(request.POST, request.FILES)  # Handle image files with request.FILES
        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.user = request.user
            kyc.save()
            messages.success(request, 'KYC verification submitted successfully and pending approval.')
            return redirect('core:home')
        else:
            messages.error(request, 'KYC verification failed. Please check the provided information and try again.')
    else:
        form = KYCVerificationForm()
    
    return render(request, 'accounts/kyc_form.html', {'form': form})



@login_required
def change_password_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        new_password = request.POST.get('new_password')

        user = get_object_or_404(User, pk=user_id)
        user.password = make_password(new_password)
        user.save()

        messages.success(request, f"Password for user {user.username} has been changed successfully.")
    
    users = User.objects.all()
    return render(request, 'accounts/change_password.html', {'users': users})





import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def register_view(request, ref_code=None):
    if request.user.is_authenticated:
        return redirect("core:home")
    
    if ref_code:
        try:
            profile = Profile.objects.get(code=ref_code)
            request.session['ref_profile'] = profile.id
        except Profile.DoesNotExist:
            logger.warning(f"No profile found for ref_code: {ref_code}")

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
                    if profile_id is not None:
                        recommended_by_profile = Profile.objects.get(id=profile_id)
                        registered_profile = Profile.objects.get(user=new_user)
                        registered_profile.recommended_by = recommended_by_profile.user
                        registered_profile.save()

                    # Send admin notification email
                    send_mail(
                        subject=f"New Registration by {new_user.get_full_name()} ({new_user.username})",
                        message=(
                            f"User Details:\n"
                            f"Full Name: {new_user.get_full_name()}\n"
                            f"Username: {new_user.username}\n"
                            f"Email: {new_user.email}\n"
                        ),
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=['orbitstockindex@gmail.com']
                    )
                        
                    return redirect("accounts:useremail")
            except Exception as e:
                logger.error(f"Error in user registration: {str(e)}")
                messages.error(request, "An error occurred during registration. Please try again.")
        else:
            logger.warning(f"Form errors - User: {user_form.errors}, Account: {account_form.errors}")
    else:
        user_form = UserRegistrationForm()
        account_form = AccountDetailsForm()

    context = {
        "title": "Create a Bank Account",
        "user_form": user_form,
        "account_form": account_form,
    }
    return render(request, "accounts/register_form.html", context)




@login_required
def edit_profile(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserProfileEditForm(request.POST, instance=request.user)
            account_form = AccountDetailsEditForm(request.POST, request.FILES, instance=request.user.account)
            if user_form.is_valid() and account_form.is_valid():
                user_form.save()
                account_form.save()
                messages.success(request, 'Your profile was successfully updated!')
                return redirect('accounts:edit_profile')
            else:
                for form in [user_form, account_form]:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field.capitalize()}: {error}")
            password_form = PasswordChangeForm(request.user)
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = request.user
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('accounts:edit_profile')
            else:
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
            user_form = UserProfileEditForm(instance=request.user)
            account_form = AccountDetailsEditForm(instance=request.user.account)
    else:
        user_form = UserProfileEditForm(instance=request.user)
        account_form = AccountDetailsEditForm(instance=request.user.account)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'account_form': account_form,
        'password_form': password_form
    })


@login_required
def useremail(request):
    return render(request, 'accounts/useremail.html')

@login_required
def login_con(request):
    return render(request, 'accounts/login_con.html')
   


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Check if the IP is localhost
    if ip in ['127.0.0.1', '::1']:
        # Try to get the IP from the HOST header
        host = request.get_host()
        if ':' in host:
            ip = host.split(':')[0]
    
    return ip


def get_country_info(ip_address):
    if ip_address in ['127.0.0.1', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return "Local", None
    
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        data = response.json()
        country_name = data.get('country_name')
        
        if country_name:
            flag_response = requests.get(f'https://restcountries.com/v3.1/name/{country_name}?fields=flags')
            flag_data = flag_response.json()
            country_flag = flag_data[0]['flags']['png'] if flag_data else None
        else:
            country_name = "Unknown"
            country_flag = None
        
        return country_name, country_flag
    except Exception as e:
        print(f"Error getting country info: {e}")
        return "Unknown", None



from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from .models import LoginHistory
from .utils import get_country_info  # Ensure this is the correct import for your utility function
from user_agents import parse
from django.core.mail import send_mail
from django.conf import settings

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_banned:
                    return JsonResponse({'status': 'error', 'message': "Your account has been suspended. Please contact support for assistance."})
                
                login(request, user)
                user_agent = parse(request.META['HTTP_USER_AGENT'])
                
                device_type = user_agent.device.family
                device_name = user_agent.device.model
                operating_system = user_agent.os.family
                browser = user_agent.browser.family
                
                ip_address = request.POST.get('ip_address', 'Unknown')
                
                country_name, country_flag = get_country_info(ip_address)
                
                LoginHistory.objects.create(
                    user=user,
                    status='Successful',
                    operating_system=operating_system,
                    browser=browser,
                    device_type=device_type,
                    device_name=device_name,
                    location=country_name,
                    ip_address=ip_address,
                    country_name=country_name,
                    country_flag=country_flag
                )

                send_mail(
                    subject=f"User Login by {user.get_full_name()} ({user.username})",
                    message=(
                        f"User Details:\n"
                        f"Full Name: {user.get_full_name()}\n"
                        f"Username: {user.username}\n"
                        f"Email: {user.email}\n"
                        f"IP Address: {ip_address}\n"
                        f"Location: {country_name}\n"
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=['orbitstockindex@gmail.com']
                )
                
                return JsonResponse({'status': 'success', 'message': f"Login Successful. Welcome back, {user.username}.", 'redirect': reverse('accounts:login_con')})
            else:
                return JsonResponse({'status': 'error', 'message': "Invalid username or password"})
        else:
            # Collect all form errors
            errors = form.errors.as_json()
            return JsonResponse({'status': 'error', 'message': errors})
    else:
        form = LoginForm()
    return render(request, 'accounts/form.html', {'form': form})
@login_required
def login_history(request):
    user_login_history = LoginHistory.objects.filter(user=request.user)
    profile = Profile.objects.get(user=request.user)
    my_recs = profile.get_recommended_profiles()
    return render(request, 'accounts/login_history.html', {'login_history': user_login_history,'my_recs':my_recs})


def logout_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    else:
        logout(request)
        return redirect("core:home")



@login_required
def select_user(request):
    users = User.objects.all()
    return render(request, 'accounts/select_user.html', {'users': users})    


@login_required
def invest_now(request):
    form = InvestmentForm(request.POST or None, initial={'schema_id': 1})  # Set initial schema_id to Plan A
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user  # Associate the investment with the current user

            # Check if the user has enough balance
            user = request.user

            # Check if the investment amount is below the minimum for the selected plan
            min_investment_amounts = {
                1: 500,  # Plan A
            }
            if investment.amount < min_investment_amounts.get(investment.schema_id, 0):
                form.add_error('amount', 'Minimum investment amount not met for the selected plan.')
            else:
                investment.save()  # Save the investment
                # Add a success message
                success_message = "Your investment request has been submitted and is being processed."
                messages.add_message(request, messages_constants.SUCCESS, success_message)
                return redirect('core:home')  # Redirect to a success page
        else:
            error_message = "There was an error in your submission. Please correct the form."
            messages.add_message(request, messages_constants.ERROR, error_message)
    else:
        form = InvestmentForm()

    return render(request, 'accounts/create_starter.html', {'form': form})


@login_required
def plan_b(request):
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            investment.schema_id = 2  # Plan B

            min_investment_amount = 1000  # Plan B minimum
            if investment.amount < min_investment_amount:
                form.add_error('amount', f'Minimum investment amount for Plan B is ${min_investment_amount}.')
            else:
                investment.save()
                success_message = "Your investment request has been submitted and is being processed."
                messages.add_message(request, messages.SUCCESS, success_message)
                return redirect('core:home')
    else:
        form = InvestmentForm(initial={'schema_id': 2})

    return render(request, 'accounts/planb.html', {'form': form})

@login_required
def plan_c(request):
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            investment.schema_id = 3  # Plan C

            min_investment_amount = 5000  # Plan C minimum
            if investment.amount < min_investment_amount:
                form.add_error('amount', f'Minimum investment amount for Plan C is ${min_investment_amount}.')
            else:
                investment.save()
                success_message = "Your investment request has been submitted and is being processed."
                messages.add_message(request, messages.SUCCESS, success_message)
                return redirect('core:home')
    else:
        form = InvestmentForm(initial={'schema_id': 3})

    return render(request, 'accounts/plan_c.html', {'form': form})

@login_required
def plan_d(request):
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            investment.schema_id = 4  # Plan D

            min_investment_amount = 30000  # Plan D minimum
            if investment.amount < min_investment_amount:
                form.add_error('amount', f'Minimum investment amount for Plan D is ${min_investment_amount}.')
            else:
                investment.save()
                success_message = "Your investment request has been submitted and is being processed."
                messages.add_message(request, messages.SUCCESS, success_message)
                return redirect('core:home')
    else:
        form = InvestmentForm(initial={'schema_id': 4})

    return render(request, 'accounts/plan_d.html', {'form': form})

@login_required
def plan_e(request):
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            investment.schema_id = 5  # Plan E

            min_investment_amount = 100000  # Plan E minimum
            if investment.amount < min_investment_amount:
                form.add_error('amount', f'Minimum investment amount for Plan E is ${min_investment_amount}.')
            else:
                investment.save()
                success_message = "Your investment request has been submitted and is being processed."
                messages.add_message(request, messages.SUCCESS, success_message)
                return redirect('core:home')
    else:
        form = InvestmentForm(initial={'schema_id': 5})

    return render(request, 'accounts/plan_e.html', {'form': form})

@login_required
def plan_f(request):
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            investment.schema_id = 6  # Plan F

            min_investment_amount = 500000  # Plan F minimum
            if investment.amount < min_investment_amount:
                form.add_error('amount', f'Minimum investment amount for Plan F is ${min_investment_amount}.')
            else:
                investment.save()
                success_message = "Your investment request has been submitted and is being processed."
                messages.add_message(request, messages.SUCCESS, success_message)
                return redirect('core:home')
    else:
        form = InvestmentForm(initial={'schema_id': 6})

    return render(request, 'accounts/plan_f.html', {'form': form})


@login_required
def investment_history(request):
    user = request.user
    investments = Investment.objects.filter(user=user)
    return render(request, 'accounts/investment_history.html', {'investments': investments})

@login_required
def schema(request):
    return render(request, 'accounts/schema.html')