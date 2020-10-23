from django.contrib.admin.filters import SimpleListFilter
from django.utils.translation import ugettext_lazy as _
from apps.verification.models import VERIFICATION_STATES
from apps.profiles.models import PROFILE_STATES
from django.db.models import Q


class UserVerificationLevelFilter(SimpleListFilter):
    title = _('User Verification Level')
    parameter_name = 'verification_level'

    def lookups(self, request, model_admin):
        return (
            (0, _('Unverified')),
            (1, _('Verified (PIN verification pending)')),
            (2, _('Verified')),
            (3, _('Max claims')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(user_verification__isnull=True)
        elif self.value() == '1':
            return queryset.filter(sms_pin_verifications__state=VERIFICATION_STATES.PENDING.value)
        elif self.value() == '2':
            return queryset.filter(Q(user_verification__state=VERIFICATION_STATES.CLAIMED.value) | Q(sms_pin_verifications__state=VERIFICATION_STATES.CLAIMED.value))
        elif self.value() == '3':
            return queryset.filter(user_verification__state=VERIFICATION_STATES.MAX_CLAIMS.value)
        return queryset.all()


class CompanyVerificationLevelFilter(UserVerificationLevelFilter):
    title = _('Company Verification Level')

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.exclude(company_verification__isnull=False).exclude(address_pin_verification__isnull=False)
        elif self.value() == '1':
            return queryset.filter(company_verification__isnull=False)
        elif self.value() == '2':
            return queryset.filter(address_pin_verification__isnull=False)
        else:
            return queryset


class CompanyVerificationLevelFilter(UserVerificationLevelFilter):
    title = _('Company Verification Level')

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.exclude(company_verification__isnull=False).exclude(address_pin_verification__isnull=False)
        elif self.value() == '1':
            return queryset.filter(company_verification__isnull=False)
        elif self.value() == '2':
            return queryset.filter(address_pin_verification__isnull=False)
        else:
            return queryset


class IsActiveFilter(SimpleListFilter):
    title = _('Show Deactivated')

    parameter_name = 'show_deactivated'

    def lookups(self, request, model_admin):
        return (
            (None, _('No')),
            ('yes', _('Yes')),
            ('all', _('All')),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'show_deactivated':
            return queryset.all()
        elif self.value() is None:
            return queryset.filter(state=PROFILE_STATES.ACTIVE.value)
