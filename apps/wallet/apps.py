from django.apps import AppConfig


class WalletsConfig(AppConfig):
    name = "apps.wallet"

    def ready(self):
        import apps.wallet.signals

        return super().ready()
