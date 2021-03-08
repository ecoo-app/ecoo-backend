from django.urls import path

from apps.currency.views import CurrencyList

urlpatterns = [
    path("currency/list/", CurrencyList.as_view(), name="currencies"),
]
