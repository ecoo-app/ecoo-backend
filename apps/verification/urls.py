from django.urls import path

from apps.currency.views import CurrencyList
from apps.verification.views import AddressPinVerificationView, AutocompleteCompanyList, AutocompleteUserList, create_paper_wallet_from_userverification, resend_user_profile_pin, verify_company_profile_pin, verify_user_profile_pin

app_name='verification'


urlpatterns = [
    path('resend_user_profile_pin/<slug:user_profile_uuid>',
         resend_user_profile_pin, name='resend_user_profile_pin'),
    path('verify_user_profile_pin/<slug:user_profile_uuid>',
         verify_user_profile_pin, name='verify_user_profile_pin'),
    path('verify_company_profile_pin/<slug:company_profile_uuid>', verify_company_profile_pin,
         name='verify_company_profile_pin'),
    path('autocomplete_user/', AutocompleteUserList.as_view(), name='autocomplete_user'),
    path('autocomplete_company/', AutocompleteCompanyList.as_view(), name='autocomplete_company'),
    path('create_paper_wallet/<uuid:uuid>',create_paper_wallet_from_userverification, name='generate_paper_wallet'),
    path('addresspinverification_detail/<uuid:pk>/',
         AddressPinVerificationView.as_view(), name='addresspinverification_detail'),
]
