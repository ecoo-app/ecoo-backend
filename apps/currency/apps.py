from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CurrencyConfig(AppConfig):
    name = 'apps.currency'
    verbose_name = _('Currency')

    def ready(self):
        import apps.currency.signals
        return super().ready()
