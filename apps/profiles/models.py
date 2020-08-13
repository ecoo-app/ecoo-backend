import secrets
import string
from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Q, Sum
from django.db.models.signals import pre_save
from django.utils.crypto import get_random_string

from project.mixins import UUIDModel
from django.utils.translation import ugettext_lazy as _

from apps.wallet.models import Wallet, WALLET_CATEGORIES


class PROFILE_VERIFICATION_STAGES(Enum):
    UNVERIFIED = 0
    PARTIALLY_VERIFIED = 1
    VERIFIED = 2


PROFILE_VERIFICATION_STAGES_CHOICES = (
    (PROFILE_VERIFICATION_STAGES.UNVERIFIED.value, _('Unverified')),
    (PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value,
     _('Verified (PIN verification pending)')),
    (PROFILE_VERIFICATION_STAGES.VERIFIED.value, _('Verified')),
)


class CompanyProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE, related_name='company_profiles')

    name = models.CharField(max_length=128)
    uid = models.CharField(max_length=15, blank=True)

    address_street = models.CharField(max_length=128, blank=True)
    address_town = models.CharField(max_length=128, blank=True)
    address_postal_code = models.CharField(max_length=128, blank=True)

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='company_profiles')
    # 0 -> no match with the verifications entries
    # 1 -> there has been a match but pin is pending
    # 2 -> match and pin fully verified

    @property
    def verification_stage(self):
        if hasattr(self, 'company_verification'):
            if self.address_pin_verification.state == 3:
                return 2
            else:
                return 1
        else:
            return 0

    @property
    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage)

    def clean(self, *args, **kwargs):
        if self.wallet.category != WALLET_CATEGORIES.COMPANY.value:
            raise ValidationError(
                "Only consumer wallets can be attached to user profiles")
        if self.owner.pk != self.wallet.owner.pk:
            raise ValidationError(
                "You can only attach a wallet you own to this profile")
        if not self.uid:
            raise ValidationError(
                "Either uid or owner information has to be filled out")
        super(CompanyProfile, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = _('Company Profiles')


class UserProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE, related_name='user_profiles')

    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)

    address_street = models.CharField(max_length=128, blank=True)
    address_town = models.CharField(max_length=128, blank=True)
    address_postal_code = models.CharField(max_length=128, blank=True)

    telephone_number = models.CharField(max_length=16)
    date_of_birth = models.DateField()

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='user_profiles')

    @property
    def verification_stage(self):
        if hasattr(self, 'user_verification'):
            if self.sms_pin_verification.state == 3:
                return 2
            else:
                return 1
        else:
            return 0

    @property
    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage)

    def clean(self, *args, **kwargs):
        if self.wallet.category != WALLET_CATEGORIES.CONSUMER.value:
            raise ValidationError(
                "Only consumer wallets can be attached to user profiles")
        if self.owner.pk != self.wallet.owner.pk:
            raise ValidationError(
                "You can only attach a wallet you own to this profile")
        if not self.telephone_number.startswith("+417"):
            raise ValidationError("Only Swiss mobile numbers are allowed")
        super(UserProfile, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = _('User Profiles')
