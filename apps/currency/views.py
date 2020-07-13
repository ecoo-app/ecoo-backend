from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.currency.models import Currency, VerificationInput
from apps.currency.serializers import (CurrencySerializer,
                                       VerificationInputSerializer)
from apps.wallet.models import Company, VerificationData, WALLET_STATES, Wallet


class CurrencyList(generics.ListAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()


class VerificationInputList(generics.ListAPIView):
    serializer_class = VerificationInputSerializer
    filterset_fields = ['currency']
    queryset = VerificationInput.objects.all()


@api_view(['POST'])
def verify(request, currency_uuid=None, company_uuid=None):
    # TODO: how to verify user for e currency with the provided input?
    verification_ok = True

    if verification_ok:
        verification_data = VerificationData.objects.create()
        if company_uuid:
            verification_data.company = Company.objects.get(uuid=company_uuid)
        verification_data.currency = Currency.objects.get(uuid=currency_uuid)
        verification_data.save()
    # where/what to store if user/company is verified for a specific currency
    return Response({"verification_data": str(verification_data.uuid)})


@api_view(['POST'])
def verify_wallet(request, wallet_id=None):
    wallet = Wallet.objects.get(walletID=wallet_id)
    # TODO: how to verify user for e currency with the provided input?
    verification_ok = True

    if verification_ok:
        wallet.state = WALLET_STATES.VERIFIED.value
        wallet.save()

    return Response({"walletID": wallet_id, "verification_ok": verification_ok})
