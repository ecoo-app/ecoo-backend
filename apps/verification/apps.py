from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class VerificationConfig(AppConfig):
    name = "apps.verification"
    verbose_name = _("Verification")

    def ready(self):
        import apps.verification.signals

        return super().ready()
