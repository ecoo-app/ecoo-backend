from django.contrib import admin

from apps.currency.models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'token_id','symbol','decimals','allow_minting','campaign_end']
    list_filter = ['allow_minting',]
