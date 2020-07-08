from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view

from apps.currency.models import Currency, VerificationInput
from apps.currency.serializers import (CurrencySerializer,
                                       VerificationInputSerializer)
from rest_framework.response import Response


class CurrencyList(generics.ListAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()


class VerificationInputList(generics.ListAPIView):
    serializer_class = VerificationInputSerializer
    filterset_fields = ['currency']
    queryset = VerificationInput.objects.all()



@api_view(['POST'])
def verify(request):
    print(request.body)
    # TODO: how to verify user for e currency with the provided input?
    # where/what to store if user/company is verified for a specific currency
    return Response({"message": "Hello, world!"})
