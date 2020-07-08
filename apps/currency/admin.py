from django.contrib import admin

from apps.currency.models import Currency, VerificationInput


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass

@admin.register(VerificationInput)
class VerificationInputAdmin(admin.ModelAdmin):
    list_display = ['currency','label','data_type']