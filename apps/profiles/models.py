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
    (PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value, _('Verified (PIN verification pending)')),
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

    def verification_stage(self):
        if hasattr(self, 'company_verification'):
            if self.company_verification.state == 3:
                return 2
            else:
                return 1
        else:
            return 0


    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage())
    verification_stage_display.short_description = _('Verification status')

    def clean(self, *args, **kwargs):
        if self.wallet.category != WALLET_CATEGORIES.COMPANY.value:
            raise ValidationError(_('Only company wallets can be attached to user profiles'))
        if self.wallet.owner is not None and self.owner.pk != self.wallet.owner.pk:
            raise ValidationError(_('You can only attach a wallet you own to this profile'))
        if not self.uid:
            raise ValidationError(_('Either uid or owner information has to be filled out'))
        super(CompanyProfile, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Company Profile')
        verbose_name_plural = _('Company Profiles')


class UserProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Owner'),
                              on_delete=models.CASCADE, related_name='user_profiles')

    first_name = models.CharField(verbose_name=_('Firstname'), max_length=128)
    last_name = models.CharField(verbose_name=_('Lastname'), max_length=128)

    address_street = models.CharField(verbose_name=_('Street'), max_length=128, blank=True)
    address_town = models.CharField(verbose_name=_('City'), max_length=128, blank=True)
    address_postal_code = models.CharField(verbose_name=_('Postcode'), max_length=128, blank=True)

    telephone_number = models.CharField(verbose_name=_('Phonenumber'), help_text=_('Format: +41 7X XXX XX XX'), max_length=16)
    date_of_birth = models.DateField(verbose_name=_('Birthdate'))

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='user_profiles')

    def verification_stage(self):
        if hasattr(self, 'user_verification'):
            if self.user_verification.state == 3:
                return 2
            else:
                return 1
        return 0

    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage())
    verification_stage_display.short_description = _('Verification status')

    def clean(self, *args, **kwargs):
        if not self.telephone_number.replace(' ', '').startswith("+417"):
            raise ValidationError(_('Only Swiss mobile numbers are allowed'))        
        if self.wallet.category != WALLET_CATEGORIES.CONSUMER.value:
            raise ValidationError(_('Only consumer wallets can be attached to user profiles'))
        if self.wallet.owner is not None and self.owner.pk != self.wallet.owner.pk:
            raise ValidationError(_('You can only attach a wallet you own to this profile'))
        super(UserProfile, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)