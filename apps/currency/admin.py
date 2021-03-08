from django.contrib import admin

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
