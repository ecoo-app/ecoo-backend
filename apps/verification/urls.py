from django.urls import path

from apps.currency.views import CurrencyList
from apps.verification.views import VerificationInputList, verify_wallet, get_verification_input

urlpatterns = [
    path('verificationinput/list/', get_verification_input,
         name='verificationinputs'),
    # path('verificationinput/list/', VerificationInputList.as_view(),
        #  name='verificationinputs'),
    path('verify/<slug:wallet_id>', verify_wallet, name='verify_wallet')
]
