from django.contrib import admin

from apps.currency.models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'token_id','symbol','decimals','allow_minting','campaign_end','created_at']
    list_filter = ['allow_minting','created_at']
    readonly_fields=['created_at',]


