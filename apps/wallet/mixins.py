from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.http.request import HttpRequest


class WalletCurrencyOwnedMixin:
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not request.user.has_perm("currency.can_view_all_currencies"):
            qs = qs.filter(
                Q(wallet__currency__users__id__exact=request.user.id)
                | Q(wallet__owner=request.user)
            )
        return qs
