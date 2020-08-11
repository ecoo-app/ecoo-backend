from django.contrib.admin.filters import SimpleListFilter
from apps.verification.models import VERIFICATION_STATES, UserVerification


class VerificaitonFilter(SimpleListFilter):
    title = 'User Verification Level'
    parameter_name = 'verification_level'

    def lookups(self, request, model_admin):
        return (
            (1, 'Level 1'),
            (2, 'Level 2'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(state=VERIFICATION_STATES.CLAIMED.value)
        elif self.value() == '2':
            users = []
            for user in queryset.filter(state=VERIFICATION_STATES.CLAIMED.value):
                if user.has_pin():
                    users.append(user.pk)
            return UserVerification.objects.filter(pk__in=users)
        else:
            return queryset