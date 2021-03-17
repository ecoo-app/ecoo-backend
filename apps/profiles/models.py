from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.wallet.models import WALLET_CATEGORIES, Wallet
from project.mixins import UUIDModel


class PROFILE_VERIFICATION_STAGES(Enum):
    UNVERIFIED = 0
    PARTIALLY_VERIFIED = 1
    VERIFIED = 2
    MAX_CLAIMS = 3


PROFILE_VERIFICATION_STAGES_CHOICES = (
    (PROFILE_VERIFICATION_STAGES.UNVERIFIED.value, _("Unverified")),
    (
        PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value,
        _("Verified (PIN verification pending)"),
    ),
    (PROFILE_VERIFICATION_STAGES.VERIFIED.value, _("Verified")),
    (PROFILE_VERIFICATION_STAGES.MAX_CLAIMS.value, _("Max Claims")),
)


class PROFILE_STATES(Enum):
    ACTIVE = 0
    DEACTIVATED = 3


PROFILE_STATE_CHOICES = (
    (PROFILE_STATES.ACTIVE.value, _("Active")),
    (PROFILE_STATES.DEACTIVATED.value, _("Deactivated")),
)


class CompanyProfile(UUIDModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
        related_name="company_profiles",
    )

    name = models.CharField(
        max_length=128,
        verbose_name=_("Name"),
    )
    uid = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_("uid"),
    )

    address_street = models.CharField(
        max_length=128,
        blank=False,
        verbose_name=_("Street"),
    )
    address_town = models.CharField(
        max_length=128,
        blank=False,
        verbose_name=_("Town"),
    )
    address_postal_code = models.CharField(
        max_length=128,
        blank=False,
        verbose_name=_("Postal code"),
    )

    phone_number = models.CharField(
        max_length=128,
        blank=True,
        validators=[
            RegexValidator(
                r"(\b(0041|0)|\B\+41)(\s?\(0\))?(\s)?[1-9]{2}(\s)?[0-9]{3}(\s)?[0-9]{2}(\s)?[0-9]{2}\b",
                _("Not a valid swiss phone number"),
            )
        ],
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="company_profiles",
        verbose_name=_("Wallet"),
    )

    state = models.IntegerField(
        _("State"), default=PROFILE_STATES.ACTIVE.value, choices=PROFILE_STATE_CHOICES
    )

    def verification_stage(self):
        from apps.verification.models import VERIFICATION_STATES

        if hasattr(self, "company_verification"):
            if self.company_verification.state == VERIFICATION_STATES.CLAIMED.value:
                return PROFILE_VERIFICATION_STAGES.VERIFIED.value
            else:
                return PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value
        else:
            return PROFILE_VERIFICATION_STAGES.UNVERIFIED.value

    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage())

    verification_stage_display.short_description = _("Verification status")

    def clean(self, *args, **kwargs):
        # TODO: do we need to clean the data? (eg. strip() on strings)
        errors = {}

        if self.state == PROFILE_STATES.DEACTIVATED.value:
            if self.verification_stage == PROFILE_VERIFICATION_STAGES.VERIFIED.value:
                errors["state"] = ValidationError(
                    _("Cannot deactivate a verified profile")
                )
        if hasattr(self, "wallet"):
            if self.wallet.category != WALLET_CATEGORIES.COMPANY.value:
                errors["wallet"] = ValidationError(
                    _("Only company wallets can be attached to company profiles")
                )

            if hasattr(self, "owner"):
                if (
                    self.wallet.owner is not None
                    and self.owner.pk != self.wallet.owner.pk
                ):
                    errors["wallet"] = ValidationError(
                        _("You can only attach your own wallet to this profile")
                    )

        if len(errors) > 0:
            raise ValidationError(errors)

        super(CompanyProfile, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        data = dict(self.__dict__)
        del data["_state"]
        del data["uuid"]
        del data["created_at"]
        del data["updated_at"]
        queryset = CompanyProfile.objects.filter(**data)
        if queryset.exists() and self not in queryset:
            raise ValidationError(_("Cannot generate same companyprofile twice"))
        super(CompanyProfile, self).save(*args, **kwargs)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Company Profile")
        verbose_name_plural = _("Company Profiles")

    def __str__(self):
        return "{}".format(
            self.name,
        )


class UserProfile(UUIDModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
        related_name="user_profiles",
    )

    first_name = models.CharField(verbose_name=_("Firstname"), max_length=128)
    last_name = models.CharField(verbose_name=_("Lastname"), max_length=128)

    address_street = models.CharField(
        verbose_name=_("Street"), max_length=128, blank=True
    )
    address_town = models.CharField(verbose_name=_("City"), max_length=128, blank=True)
    address_postal_code = models.CharField(
        verbose_name=_("Postcode"), max_length=128, blank=True
    )

    telephone_number = models.CharField(
        verbose_name=_("Phonenumber"),
        help_text=_("Format: +41 7X XXX XX XX"),
        max_length=16,
    )
    date_of_birth = models.DateField(verbose_name=_("Birthdate"))

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="user_profiles"
    )
    place_of_origin = models.CharField(
        max_length=128, verbose_name=_("Place of origin")
    )

    state = models.IntegerField(
        _("State"), default=PROFILE_STATES.ACTIVE.value, choices=PROFILE_STATE_CHOICES
    )

    @property
    def sms_pin_verification(self):
        from apps.verification.models import VERIFICATION_STATES

        if self.sms_pin_verifications.filter(
            state=VERIFICATION_STATES.PENDING.value
        ).exists():
            return self.sms_pin_verifications.filter(
                state=VERIFICATION_STATES.PENDING.value
            ).last()

    def verification_stage(self):
        if hasattr(self, "user_verification"):
            from apps.verification.models import VERIFICATION_STATES

            if self.user_verification.state == VERIFICATION_STATES.CLAIMED.value:
                return PROFILE_VERIFICATION_STAGES.VERIFIED.value
            elif self.user_verification.state == VERIFICATION_STATES.MAX_CLAIMS.value:
                return PROFILE_VERIFICATION_STAGES.MAX_CLAIMS.value
            else:
                return PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value
        else:
            return PROFILE_VERIFICATION_STAGES.UNVERIFIED.value

    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage())

    verification_stage_display.short_description = _("Verification status")

    def clean(self, *args, **kwargs):
        # TODO: additional cleanup (eg. phonenumbers without spaces/always with spaces formatted, Street without trailing/leading spaces etc.)
        errors = {}
        if self.state == PROFILE_STATES.DEACTIVATED.value:
            if self.verification_stage == PROFILE_VERIFICATION_STAGES.VERIFIED.value:
                errors["state"] = ValidationError(
                    _("Cannot deactivate a verified profile")
                )
        # TODO: this isn't sufficient to be sure that it's a swiss mobile number
        if not self.telephone_number.replace(" ", "").startswith("+417"):
            errors["telephone_number"] = ValidationError(
                _("Only Swiss mobile numbers are allowed")
            )

        if hasattr(self, "wallet"):
            if self.wallet.category != WALLET_CATEGORIES.CONSUMER.value:
                errors["wallet"] = ValidationError(
                    _("Only consumer wallets can be attached to user profiles")
                )

            if hasattr(self, "owner"):
                if (
                    self.wallet.owner is not None
                    and self.owner.pk != self.wallet.owner.pk
                ):
                    errors["wallet"] = ValidationError(
                        _("You can only attach your own wallet to this profile")
                    )

        if len(errors) > 0:
            raise ValidationError(errors)

        super(UserProfile, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        data = dict(self.__dict__)
        del data["_state"]
        del data["uuid"]
        del data["created_at"]
        del data["updated_at"]
        queryset = UserProfile.objects.filter(**data)
        if queryset.exists() and self not in queryset:
            raise ValidationError(_("Cannot generate same userprofile twice"))
        super(UserProfile, self).save(*args, **kwargs)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)
