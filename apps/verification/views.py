from django.shortcuts import render
# from requests.models import Response
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.decorators import api_view

from apps.verification.serializers import (VerificationInputDataSerializer,
                                           VerificationInputSerializer)
from apps.wallet.models import WALLET_STATES, Wallet

from apps.verification.models import VerificationInput


class VerificationInputList(generics.ListAPIView):
    serializer_class = VerificationInputSerializer
    filterset_fields = ['currency__uuid', 'used_for_companies']
    queryset = VerificationInput.objects.all()


@api_view(['POST'])
def verify_wallet(request, walletID=None):
    wallet = Wallet.objects.get(walletID=walletID)
    # TODO: how to verify user for e currency with the provided input?
    print('request.data')
    print(request.data)

    # inputs = VerificationInputDataSerializer(request.data, many=True)
    verification_ok = True

    if verification_ok:
        wallet.state = WALLET_STATES.VERIFIED.value
        wallet.save()
    else:
        # TODO: what error / exception should be raised if validaiton failed?
        pass

    return Response({"walletID": walletID, "verification_ok": verification_ok})
