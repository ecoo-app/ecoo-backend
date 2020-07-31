import os
import sys

from project.base_settings import *

# ADMINS = [('??', '??@??'),]

# Postgres DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DJANGO_DB_NAME', 'postgres'),
        'USER': os.environ.get('DJANGO_DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DJANGO_DB_HOST', 'postgres')
    }
}

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase'
    }

MEDIA_ROOT = "/code/media/"
STATIC_ROOT = "/code/static_root/"
STATICFILES_DIRS = [
    '/code/static',
]

EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '?')
EMAIL_PORT = os.environ.get('DJANGO_EMAIL_PORT', '587')
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_USER', '?')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_PASSWORD', '?')
EMAIL_USE_TLS = os.environ.get(
    'DJANGO_USE_TLS', 'true').lower() in ('true', 'yes', '1')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '?')

DEBUG = os.environ.get('DJANGO_DEBUG', 'false').lower() in ('true', 'yes', '1')

ALLOWED_HOSTS = ['*']

# OAUTH
# Your client_id com.application.your, aka "Service ID"
SOCIAL_AUTH_APPLE_ID_CLIENT = os.environ.get('APPLE_ID_CLIENT', '?')
SOCIAL_AUTH_APPLE_ID_TEAM = os.environ.get(
    'APPLE_ID_TEAM', '?')  # Your Team ID, ie K2232113
SOCIAL_AUTH_APPLE_ID_KEY = os.environ.get(
    'APPLE_ID_KEY', '?')  # Your Key ID, ie Y2P99J3N81K
SOCIAL_AUTH_APPLE_ID_SECRET = os.environ.get('APPLE_ID_SECRET', '?')

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_OAUTH2_KEY', '?')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_OAUTH2_SECRET', '?')

# FCM
FCM_DJANGO_SETTINGS["FCM_SERVER_KEY"] = os.environ.get('FCM_KEY', '?')