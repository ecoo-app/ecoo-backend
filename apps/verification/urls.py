from django.urls import path

from apps.currency.views import CurrencyList
from apps.verification.views import VerificationInputList, verify_wallet

urlpatterns = [
    path('verificationinput/list/', VerificationInputList.as_view(),
         name='verificationinputs'),
    path('verify/<slug:wallet_id>', verify_wallet, name='verify_wallet')
]
