from django.contrib import admin, messages
from apps.profiles.models import UserProfile, CompanyProfile
from django.utils.translation import ugettext_lazy as _
import requests
from django.conf import settings
from django import forms
import datetime
from django.shortcuts import render
from apps.profiles.filters import VerificationLevelFilter
from apps.verification.models import UserVerification, CompanyVerification, VERIFICATION_STATES
from apps.wallet.models import Wallet

def verify_users(modeladmin, request, queryset):

    modified = 0
    for user_profile in queryset.exclude(user_verification__isnull=False).exclude(sms_pin_verification__isnull=False):
        UserVerification.objects.create(
            user_profile=user_profile,
            state=VERIFICATION_STATES.CLAIMED.value,
            first_name=user_profile.first_name,
            last_name=user_profile.last_name,
            address_street=user_profile.address_street,
            address_town=user_profile.address_town,
            address_postal_code=user_profile.address_postal_code,
            date_of_birth=user_profile.date_of_birth,
        )
        user_profile.save()

        from apps.wallet.utils import create_claim_transaction
        create_claim_transaction(user_profile.wallet)

        modified += 1

    if modified > 0:
        messages.add_message(request, messages.SUCCESS, _('{} User Profiles verified').format(modified))
    else:
        messages.add_message(request, messages.WARNING, _('All User Profiles were already verified'))

verify_users.short_description = _('Verify users')


def verify_companies(modeladmin, request, queryset):

    modified = 0
    for company_profile in queryset.exclude(company_verification__isnull=False):
        CompanyVerification.objects.create(
            company_profile=company_profile,
            state=VERIFICATION_STATES.CLAIMED.value,
            name=company_profile.name,
            uid=company_profile.uid,
        )

        company_profile.save()
        modified += 1

    if modified > 0:
        messages.add_message(request, messages.SUCCESS, _('{} Company Profiles verified').format(modified))
    else:
        messages.add_message(request, messages.WARNING, _('All Company Profiles were already verified'))

verify_companies.short_description = _('Verify companies')

class PreventDeleteWhenVerifiedMixin:
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            # disallow delete if state != unverified
            return obj.verification_stage() == 0
        return True

@admin.register(UserProfile)
class UserProfile(PreventDeleteWhenVerifiedMixin, admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'address_street', 'telephone_number', 'date_of_birth', 'verification_stage_display','created_at']
    search_fields = ['first_name', 'last_name',
                     'address_street', 'telephone_number', 'date_of_birth']
    list_filter = [VerificationLevelFilter,'created_at']
    actions = [verify_users]
    readonly_fields=['created_at',]


    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['wallet'].queryset = Wallet.objects.filter(category=0)
        return super(UserProfile, self).render_change_form(request, context, *args, **kwargs)

@admin.register(CompanyProfile)
class CompanyProfile(PreventDeleteWhenVerifiedMixin, admin.ModelAdmin):
    list_display = ['name', 'uid', 'address_street', 'verification_stage_display', 'created_at']
    search_fields = ['name', 'uid',
                     'address_street']
    list_filter = [VerificationLevelFilter,'created_at']
    actions = [verify_companies]
    readonly_fields=['created_at',]

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['wallet'].queryset = Wallet.objects.filter(category=1)
        return super(CompanyProfile, self).render_change_form(request, context, *args, **kwargs)