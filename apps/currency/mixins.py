
from django.db import models

from apps.currency.models import Currency
from project.mixins import UUIDModel


class CurrencyOwnedMixin(UUIDModel):
    currency = models.ForeignKey(
        Currency, on_delete=models.SET_NULL, null=True,)

    class Meta:
        abstract = True
