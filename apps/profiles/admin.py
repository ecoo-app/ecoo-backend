import datetime

import requests
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from apps.profiles.filters import (
    CompanyVerificationLevelFilter,
    IsActiveFilter,
    UserVerificationLevelFilter,
)
from apps.profiles.models import (
    PROFILE_STATES,
    PROFILE_VERIFICATION_STAGES,
    CompanyProfile,
    UserProfile,
)
from apps.verification.models import (
    VERIFICATION_STATES,
    CompanyVerification,
    PlaceOfOrigin,
    UserVerification,
)
from apps.wallet.models import WALLET_STATES, Wallet


def verify_users(modeladmin, request, queryset):

    modified = 0
    for user_profile in queryset.exclude(sms_pin_verifications__isnull=False):
        if not user_profile.verification_stage() in [
            PROFILE_VERIFICATION_STAGES.UNVERIFIED.value,
            PROFILE_VERIFICATION_STAGES.MAX_CLAIMS.value,
        ]:
            continue

        if hasattr(user_profile, "user_verification"):
            user_profile.user_verification.state = VERIFICATION_STATES.CLAIMED.value
            user_profile.user_verification.save()
        else:
            user_verification = UserVerification.objects.create(
                user_profile=user_profile,
                state=VERIFICATION_STATES.CLAIMED.value,
                first_name=user_profile.first_name,
                last_name=user_profile.last_name,
                address_street=user_profile.address_street,
                address_town=user_profile.address_town,
                address_postal_code=user_profile.address_postal_code,
                date_of_birth=user_profile.date_of_birth,
            )
            PlaceOfOrigin.objects.create(
                place_of_origin=user_profile.place_of_origin,
                user_verification=user_verification,
            )
            user_profile.save()

        if user_profile.wallet.state != WALLET_STATES.VERIFIED.value:
            user_profile.wallet.state = WALLET_STATES.VERIFIED.value
            user_profile.wallet.save()

        from apps.wallet.utils import create_claim_transaction

        create_claim_transaction(user_profile.wallet)

        modified += 1

    if modified > 0:
        messages.add_message(
            request, messages.SUCCESS, _("{} User Profiles verified").format(modified)
        )
    else:
        messages.add_message(
            request, messages.WARNING, _("All User Profiles were already verified")
        )


verify_users.short_description = _("Verify users")


def verify_companies(modeladmin, request, queryset):

    modified = 0
    for company_profile in queryset.exclude(company_verification__isnull=False):
        CompanyVerification.objects.create(
            company_profile=company_profile,
            state=VERIFICATION_STATES.CLAIMED.value,
            name=company_profile.name,
            uid=company_profile.uid,
            address_street=company_profile.address_street,
            address_town=company_profile.address_town,
            address_postal_code=company_profile.address_postal_code,
        )

        company_profile.save()

        if company_profile.wallet.state != WALLET_STATES.VERIFIED.value:
            company_profile.wallet.state = WALLET_STATES.VERIFIED.value
            company_profile.wallet.save()

        modified += 1

    if modified > 0:
        messages.add_message(
            request,
            messages.SUCCESS,
            _("{} Company Profiles verified").format(modified),
        )
    else:
        messages.add_message(
            request, messages.WARNING, _("All Company Profiles were already verified")
        )


verify_companies.short_description = _("Verify companies")


def deactivate_company_profile(modeladmin, request, queryset):
    queryset.exclude(
        company_verification__state=VERIFICATION_STATES.CLAIMED.value
    ).update(state=PROFILE_STATES.DEACTIVATED.value)


deactivate_company_profile.short_description = _("Deactivate Company Profile")


def deactivate_user_profile(modeladmin, request, queryset):
    queryset.exclude(user_verification__state=VERIFICATION_STATES.CLAIMED.value).update(
        state=PROFILE_STATES.DEACTIVATED.value
    )


deactivate_user_profile.short_description = _("Deactivate User Profile")


class PreventDeleteWhenVerifiedMixin:
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return (
                obj.verification_stage() == PROFILE_VERIFICATION_STAGES.UNVERIFIED.value
            )
        return True


@admin.register(UserProfile)
class UserProfile(PreventDeleteWhenVerifiedMixin, admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "address_street",
        "telephone_number",
        "date_of_birth",
        "owner",
        "verification_stage_display",
        "created_at",
    ]
    search_fields = [
        "first_name",
        "last_name",
        "address_street",
        "telephone_number",
        "date_of_birth",
        "owner__username",
    ]
    list_filter = [IsActiveFilter, UserVerificationLevelFilter, "created_at"]
    actions = [deactivate_user_profile, verify_users]
    readonly_fields = [
        "created_at",
    ]

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields["wallet"].queryset = Wallet.objects.filter(
            category=0
        )
        return super(UserProfile, self).render_change_form(
            request, context, *args, **kwargs
        )


@admin.register(CompanyProfile)
class CompanyProfile(PreventDeleteWhenVerifiedMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "uid",
        "address_street",
        "owner",
        "verification_stage_display",
        "created_at",
    ]
    search_fields = ["name", "uid", "address_street", "owner__username"]
    list_filter = [IsActiveFilter, CompanyVerificationLevelFilter, "created_at"]
    actions = [deactivate_company_profile, verify_companies]
    readonly_fields = [
        "created_at",
    ]

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields["wallet"].queryset = Wallet.objects.filter(
            category=1
        )
        return super(CompanyProfile, self).render_change_form(
            request, context, *args, **kwargs
        )
