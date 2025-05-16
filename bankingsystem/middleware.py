#middleware.py
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
class BannedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_banned:
            logout(request)  # Log the user out
            messages.error(request, "Your account has been suspended. Please contact support for assistance.")
            return redirect('accounts:login')  # Adjust this to your login URL name
        return self.get_response(request)