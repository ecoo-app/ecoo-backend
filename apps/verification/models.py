from enum import Enum

from django.db import models

from apps.currency.mixins import CurrencyOwnedMixin
from apps.wallet.models import Wallet
from apps.profiles.models import CompanyProfile, UserProfile
from project.mixins import UUIDModel


class VERIFICATION_STATES(Enum):
    OPEN = 1
    PENDING = 2
    CLAIMED = 3
    FAILED = 5


VERIFICATION_STATES_CHOICES = (
    (VERIFICATION_STATES.OPEN.value, 'Open'),
    (VERIFICATION_STATES.PENDING.value, 'Pending'),
    (VERIFICATION_STATES.CLAIMED.value, 'Claimed'),
    (VERIFICATION_STATES.FAILED.value, 'Failes')
)


class AbstractVerification(UUIDModel):
    state = models.IntegerField(
        choices=VERIFICATION_STATES_CHOICES, default=VERIFICATION_STATES.OPEN.value)

    class Meta:
        abstract = True


class CompanyVerification(AbstractVerification):
    company_profile = models.OneToOneField(
        CompanyProfile, on_delete=models.SET_NULL, related_name='company_verification', blank=True, null=True)

    name = models.CharField(max_length=128)
    uid = models.CharField(max_length=15)


class UserVerification(AbstractVerification):
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.SET_NULL, related_name='user_verification', blank=True, null=True)

    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)

    address_street = models.CharField(max_length=128)
    address_town = models.CharField(max_length=128)
    address_postal_code = models.CharField(max_length=128)

    date_of_birth = models.DateField()

    def has_pin(self):
        return 0 < SMSPinVerification.objects.filter(user_profile=self.user_profile, state=VERIFICATION_STATES.CLAIMED.value).count()


class AddressPinVerification(AbstractVerification):
    company_profile = models.OneToOneField(
        CompanyProfile, on_delete=models.CASCADE, related_name='address_pin_verification')

    pin = models.CharField(max_length=8, blank=True)


class SMSPinVerification(AbstractVerification):
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name='sms_pin_verification')

    pin = models.CharField(max_length=8, blank=True)
