from enum import Enum

from django.db import models

from apps.currency.mixins import CurrencyOwnedMixin
from apps.wallet.models import Wallet
from apps.profiles.models import CompanyProfile, UserProfile
from project.mixins import UUIDModel
from django.utils.translation import gettext as _


class VERIFICATION_STATES(Enum):
    OPEN = 1
    PENDING = 2
    CLAIMED = 3
    FAILED = 5


VERIFICATION_STATES_CHOICES = (
    (VERIFICATION_STATES.OPEN.value, _('Open')),
    (VERIFICATION_STATES.PENDING.value, _('Pending')),
    (VERIFICATION_STATES.CLAIMED.value, _('Claimed')),
    (VERIFICATION_STATES.FAILED.value, _('Failes'))
)


class AbstractVerification(UUIDModel):
    state = models.IntegerField(verbose_name=_(
        'State'), choices=VERIFICATION_STATES_CHOICES, default=VERIFICATION_STATES.OPEN.value)

    class Meta:
        abstract = True


class CompanyVerification(AbstractVerification):
    company_profile = models.OneToOneField(
        CompanyProfile, on_delete=models.SET_NULL, related_name='company_verification', blank=True, null=True)
    name = models.CharField(verbose_name=_('Name'), max_length=128)
    uid = models.CharField(verbose_name=_('Uid'), max_length=15,)

    class Meta:
        verbose_name = _('Company verification')
        verbose_name_plural = _('Company verifications')


class UserVerification(AbstractVerification):
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.SET_NULL, related_name='user_verification', blank=True, null=True)

    first_name = models.CharField(verbose_name=_('Firstname'), max_length=128)
    last_name = models.CharField(verbose_name=_('Lastname'), max_length=128)

    address_street = models.CharField(verbose_name=_('Street'), max_length=128)
    address_town = models.CharField(verbose_name=_('Town'), max_length=128)
    address_postal_code = models.CharField(
        verbose_name=_('Postal code'), max_length=128)

    date_of_birth = models.DateField(verbose_name=_('Date of birth'))

    class Meta:
        verbose_name = _('User verification')
        verbose_name_plural = _('User verifications')


class AddressPinVerification(AbstractVerification):
    company_profile = models.OneToOneField(
        CompanyProfile, on_delete=models.CASCADE, related_name='address_pin_verification')
    pin = models.CharField(verbose_name=_('Pin'), max_length=8, blank=True)

    class Meta:
        verbose_name = _('Adress pin verification')
        verbose_name_plural = _('Adress pin verifications')


class SMSPinVerification(AbstractVerification):
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name='sms_pin_verification')
    pin = models.CharField(verbose_name=_('Pin'), max_length=8, blank=True)

    class Meta:
        verbose_name = _('SMS pin verification')
        verbose_name_plural = _('SMS pin verifications')
