from datetime import date

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.currency.models import Currency


class CurrencyOwnedFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Currency")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "currency"

    def lookups(self, request, model_admin):
        currencies = Currency.get_currencies_to_user(request.user)
        result = []

        for currency in currencies:
            result.append((str(currency.pk), str(currency)))

        return result

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() is not None:
            return queryset.filter(currency__pk=self.value())

        return queryset
