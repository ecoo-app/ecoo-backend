from django.contrib.admin.filters import SimpleListFilter
from django.utils.translation import gettext as _


class VerificationLevelFilter(SimpleListFilter):
    title = _('User Verification Level')
    parameter_name = 'verification_level'

    def lookups(self, request, model_admin):
        return (
            (0, _('Unverified')),
            (1, _('Verified (PIN verification pending)')),
            (2, _('Verified')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.exclude(user_verification__isnull=False).exclude(sms_pin_verification__isnull=False)
        elif self.value() == '1':
            return queryset.filter(user_verification__isnull=False)
        elif self.value() == '2':
            return queryset.filter(sms_pin_verification__isnull=False)
        else:
            return queryset
