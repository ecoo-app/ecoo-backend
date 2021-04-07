from rest_framework import generics

from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from project.utils import CustomCursorPaginationReversed


class CurrencyList(generics.ListAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    pagination_class = CustomCursorPaginationReversed
