import os

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

MEDIA_ROOT = "/code/media/"
STATIC_ROOT = "/code/static_root/"
STATICFILES_DIRS = [
     '/code/static',
]

# I know, it shouldn't be here, will be removed later
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '?')
EMAIL_PORT = os.environ.get('DJANGO_EMAIL_PORT', '587')
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_USER', '?')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_PASSWORD', '?')
EMAIL_USE_TLS = os.environ.get('DJANGO_USE_TLS', 'true').lower() in ('true', 'yes', '1')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '?')

DEBUG = os.environ.get('DJANGO_DEBUG', 'false').lower() in ('true', 'yes', '1')

ALLOWED_HOSTS = ['*']
