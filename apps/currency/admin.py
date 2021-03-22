from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from apps.currency.models import Currency, PayoutAccount


class PayoutAccountInline(admin.StackedInline):
    model = PayoutAccount
    fields = [
        "name",
        "iban",
        "bank_clearing_number",
        "payout_notes",
    ]


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    inlines = [PayoutAccountInline]
    filter_horizontal = ("users",)

    list_display = [
        "name",
        "token_id",
        "symbol",
        "decimals",
        "allow_minting",
        "campaign_end",
        "created_at",
    ]
    list_filter = ["allow_minting", "created_at"]
    readonly_fields = [
        "created_at",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not (
            request.user.has_perm("currency.can_view_all_currencies")
            or request.user.is_superuser
        ):
            qs = qs.filter(users__id__exact=request.user.id)
        return qs
