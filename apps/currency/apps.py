from django.apps import AppConfig


class CurrencyConfig(AppConfig):
    name = 'apps.currency'

    def ready(self):
        import apps.currency.signals
        return super().ready()
