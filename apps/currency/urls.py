from django.urls import path

from apps.currency.views import CurrencyList, VerificationInputList, verify

urlpatterns = [
    path('currency/list/', CurrencyList.as_view(), name='currencies'),
    path('verificationinput/list/', VerificationInputList.as_view(),
         name='verificationinputs'),
    path('verify/', verify, name='verify')
]
