from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    name = 'apps.profiles'

    def ready(self):
        import apps.profiles.signals
        return super().ready()
