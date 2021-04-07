from rest_framework import generics

from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer


class CurrencyList(generics.ListAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all().order_by("-created_at")
