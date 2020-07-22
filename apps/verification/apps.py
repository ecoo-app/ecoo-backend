from django.apps import AppConfig


class VerificationConfig(AppConfig):
    name = 'apps.verification'

    def ready(self):
        import apps.verification.signals
        return super().ready()
