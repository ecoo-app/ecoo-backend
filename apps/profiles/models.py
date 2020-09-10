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
    MAX_CLAIMS = 3


PROFILE_VERIFICATION_STAGES_CHOICES = (
    (PROFILE_VERIFICATION_STAGES.UNVERIFIED.value, _('Unverified')),
    (PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value,
     _('Verified (PIN verification pending)')),
    (PROFILE_VERIFICATION_STAGES.VERIFIED.value, _('Verified')),
    (PROFILE_VERIFICATION_STAGES.MAX_CLAIMS.value, _('Max Claims')),
)


class CompanyProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_(
        'Owner'), on_delete=models.CASCADE, related_name='company_profiles')

    name = models.CharField(max_length=128, verbose_name=_('Name'),)
    uid = models.CharField(max_length=15, blank=True, verbose_name=_('uid'),)

    address_street = models.CharField(
        max_length=128, blank=True, verbose_name=_('Street'),)
    address_town = models.CharField(
        max_length=128, blank=True, verbose_name=_('Town'),)
    address_postal_code = models.CharField(
        max_length=128, blank=True, verbose_name=_('Postal code'),)

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE,
                               related_name='company_profiles', verbose_name=_('Wallet'),)

    def verification_stage(self):
        from apps.verification.models import VERIFICATION_STATES
        if hasattr(self, 'company_verification'):
            if self.company_verification.state == VERIFICATION_STATES.CLAIMED.value:
                return PROFILE_VERIFICATION_STAGES.VERIFIED.value
            else:
                return PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value
        else:
            return PROFILE_VERIFICATION_STAGES.UNVERIFIED.value

    def verification_stage_display(self):
        return dict(PROFILE_VERIFICATION_STAGES_CHOICES).get(self.verification_stage())
    verification_stage_display.short_description = _('Verification status')

    def clean(self, *args, **kwargs):
        if self.wallet.category != WALLET_CATEGORIES.COMPANY.value:
            raise ValidationError(
                _('Only company wallets can be attached to company profiles'))
        if self.wallet.owner is not None and self.owner.pk != self.wallet.owner.pk:
            raise ValidationError(
                _('You can only attach a wallet you own to this profile'))
        if not self.address_street or not self.address_postal_code or not self.address_town or not self.name:
            raise ValidationError(
                _('Address needs to be filled out completely'))
        # if not self.uid:
            # raise ValidationError(_('Either uid or owner information has to be filled out'))
        super(CompanyProfile, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        data = dict(self.__dict__)
        del data['_state']
        del data['uuid']
        del data['created_at']
        del data['updated_at']
        queryset = CompanyProfile.objects.filter(**data)
        if queryset.exists() and not self in queryset:
            raise ValidationError(
                _('Cannot generate same companyprofile twice'))
        super(CompanyProfile, self).save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Company Profile')
        verbose_name_plural = _('Company Profiles')

    def __str__(self):
        return '{}'.format(self.name,)


class UserProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Owner'),
                              on_delete=models.CASCADE, related_name='user_profiles')

    first_name = models.CharField(verbose_name=_('Firstname'), max_length=128)
    last_name = models.CharField(verbose_name=_('Lastname'), max_length=128)

    address_street = models.CharField(
        verbose_name=_('Street'), max_length=128, blank=True)
    address_town = models.CharField(
        verbose_name=_('City'), max_length=128, blank=True)
    address_postal_code = models.CharField(
        verbose_name=_('Postcode'), max_length=128, blank=True)

    telephone_number = models.CharField(verbose_name=_(
        'Phonenumber'), help_text=_('Format: +41 7X XXX XX XX'), max_length=16)
    date_of_birth = models.DateField(verbose_name=_('Birthdate'))

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='user_profiles')

    @property
    def sms_pin_verification(self):
        from apps.verification.models import VERIFICATION_STATES
        if self.sms_pin_verifications.filter(state=VERIFICATION_STATES.PENDING.value).exists():
            return self.sms_pin_verifications.filter(state=VERIFICATION_STATES.PENDING.value).last()

    def verification_stage(self):
        if hasattr(self, 'user_verification'):
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
    verification_stage_display.short_description = _('Verification status')

    def clean(self, *args, **kwargs):
        # TODO: this isn't sufficient to be sure that it's a swiss mobile number
        # additionally verfication should be done on the field and not on the model
        if not self.telephone_number.replace(' ', '').startswith("+417"):
            raise ValidationError(_('Only Swiss mobile numbers are allowed'))
        if self.wallet.category != WALLET_CATEGORIES.CONSUMER.value:
            raise ValidationError(
                _('Only consumer wallets can be attached to user profiles'))
        if self.wallet.owner is not None and self.owner.pk != self.wallet.owner.pk:
            raise ValidationError(
                _('You can only attach a wallet you own to this profile'))
        super(UserProfile, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        data = dict(self.__dict__)
        del data['_state']
        del data['uuid']
        del data['created_at']
        del data['updated_at']
        queryset = UserProfile.objects.filter(**data)
        if queryset.exists() and not self in queryset:
            raise ValidationError(_('Cannot generate same userprofile twice'))
        super(UserProfile, self).save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)
