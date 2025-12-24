

from django.urls import include, path
from . views import *

app_name = 'core'

urlpatterns = [
    # Redirect to the registration page if ref_code is present, otherwise, go to home
    path('', home, name='home'),
    path('home/', home, name='home'),
    
    # Handle the case with ref_code
    path('ref/<str:ref_code>/', index, name='index'),
]

