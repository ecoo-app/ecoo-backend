from django.urls import path

from apps.currency.views import CurrencyList
from apps.verification.views import verify_company_profile_pin, verify_user_profile_pin, resend_user_profile_pin

urlpatterns = [
    path('resend_user_profile_pin/<slug:user_profile_uuid>',
         resend_user_profile_pin, name='resend_user_profile_pin'),
    path('verify_user_profile_pin/<slug:user_profile_uuid>',
         verify_user_profile_pin, name='verify_user_profile_pin'),
    path('verify_company_profile_pin/<slug:company_profile_uuid>', verify_company_profile_pin,
         name='verify_company_profile_pin')
]
