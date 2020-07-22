from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import Company, WALLET_STATES, Wallet


class CurrencyList(generics.ListAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
