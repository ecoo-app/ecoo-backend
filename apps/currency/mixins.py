from django.contrib import admin
from django.db import models
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from apps.currency.models import Currency
from project.mixins import UUIDModel


class CurrencyOwnedMixin(UUIDModel):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class CurrencyOwnedAdminMixin:
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not (
            request.user.has_perm("can_view_all_currencies")
            or request.user.is_superuser
        ):
            qs = qs.filter(currency__users__id__exact=request.user.id)
        return qs
