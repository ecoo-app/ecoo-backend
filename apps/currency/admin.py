from django.contrib import admin

from apps.currency.models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass
