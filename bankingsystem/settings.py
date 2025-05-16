
import os
from pathlib import Path
#import django_heroku

import cloudinary
import cloudinary.uploader
import cloudinary.api

from django.contrib.messages import constants as messages
import dj_database_url
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent
CSRF_TRUSTED_ORIGINS = [
    "https://web-production-f4d8.up.railway.app",
    "https://www.zorevinacart.store"
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')_z--t-qq1=s!l*c-1pg(%$3l%=ys9m7!fh@jtom47ozn-24^*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'admin_soft.apps.AdminSoftDashboardConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'core',
    'transactions',
    'rest_framework',
    "corsheaders",
    'storages',
    'django.contrib.humanize',

]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    "corsheaders.middleware.CorsMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = "/accounts/login/?next="

ROOT_URLCONF = 'bankingsystem.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'core.custom_context_processors.recommended_users',
                'core.custom_context_processors.notifications',
                'core.custom_context_processors.transaction_history',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bankingsystem.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASE_URL = "postgresql://postgres.zbigkfdfdlzvimfljcsh:[Firstwork51a51$@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
# Configure the default database using the DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL)
}



"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'Firstwork51a51$',
        'HOST': 'db.pdhyxdxmgxswuxhxnlsl.supabase.co',
        'PORT': '5432',
        'DISABLE_SERVER_SIDE_CURSORS': True,
    }
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""
# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,  # Change this to your desired minimum password length
        },
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATICSTORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

#django_heroku.settings(locals())


MESSAGE_TAGS = {
    messages.SUCCESS: 'alert-success',
    messages.ERROR: 'alert-danger',
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.AccountNoBackend',
)


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

cloudinary.config( 
    cloud_name = "dro8yxudy", 
    api_key = "999164289732464", 
    api_secret = "3whimsuxvp26W1y1umnoBHdpc1U", 
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# Use the SMTP backend


# Email configuration using SSL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 465  # SSL Port
EMAIL_USE_SSL = True  # Use SSL instead of TLS
EMAIL_HOST_USER = 'info@orbit-stockindex.com'
EMAIL_HOST_PASSWORD = 'Orbitstock51a51$$'
DEFAULT_FROM_EMAIL = 'info@orbit-stockindex.com'

