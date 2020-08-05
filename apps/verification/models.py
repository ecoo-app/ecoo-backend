from enum import Enum

from django.db import models

from apps.currency.mixins import CurrencyOwnedMixin
from apps.wallet.models import Wallet
from project.mixins import UUIDModel


class VERIFICATION_STATES(Enum):
    OPEN = 1
    CLAIMED = 2
    REQUESTED = 3
    CLAIM_LIMIT_REACHED = 4
    DOUBLE_CLAIM = 5


VERIFICATION_STATES_CHOICES = (
    (VERIFICATION_STATES.OPEN.value, 'Open'),
    (VERIFICATION_STATES.CLAIMED.value, 'Claimed'),
    (VERIFICATION_STATES.REQUESTED.value, 'Requested'),
    (VERIFICATION_STATES.CLAIM_LIMIT_REACHED.value, 'Claim limit reached'),
    (VERIFICATION_STATES.DOUBLE_CLAIM.value, 'Tried to claim again'),
)


class VerificationEntry(UUIDModel):
    state = models.IntegerField(choices=VERIFICATION_STATES_CHOICES, default=1)


class VERIFICATION_INPUT_TYPES(Enum):
    TEXT = 1
    BOOLEAN = 2
    NUMBER = 3
    DATE = 4


VERIFICATION_INPUT_TYPE_CHOICES = (
    (VERIFICATION_INPUT_TYPES.TEXT.value, 'Text'),
    (VERIFICATION_INPUT_TYPES.BOOLEAN.value, 'Boolean'),
    (VERIFICATION_INPUT_TYPES.NUMBER.value, 'Date'),
    (VERIFICATION_INPUT_TYPES.DATE.value, 'Number'),
)


class VerificationInput(CurrencyOwnedMixin):
    used_for_companies = models.BooleanField(default=False)
    input_type = models.IntegerField(
        choices=VERIFICATION_INPUT_TYPE_CHOICES, default=1)
    name = models.CharField(max_length=64)
    csv_col = models.CharField(max_length=64, blank=True, null=True)


class VerificationInputData(UUIDModel):
    verification_entry = models.ForeignKey(
        VerificationEntry, on_delete=models.CASCADE)
    verification_input = models.ForeignKey(
        VerificationInput, on_delete=models.CASCADE)
    data = models.CharField(max_length=128)


class AbstractVerificationEntry(CurrencyOwnedMixin):
    state = models.IntegerField(
        choices=VERIFICATION_STATES_CHOICES, default=VERIFICATION_STATES.OPEN.value)

    class Meta:
        abstract = True

    def get_fields(self):
        return [(field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields]        


class CompanyVerification(AbstractVerificationEntry):
    name = models.CharField(max_length=128)
    uid = models.CharField(max_length=15, blank=True, null=True)
    owner_name = models.CharField(max_length=128, blank=True, null=True)
    owner_address = models.CharField(max_length=128, blank=True, null=True)
    owner_telephone_number = models.CharField(
        max_length=128, blank=True, null=True)
    receiving_wallet = models.ForeignKey(
        Wallet, blank=True, null=True, on_delete=models.SET_NULL, related_name='company_claims')

    @staticmethod
    def to_verification_input_dict():
        return [
            {'label':'name', 'type': 'text'},
            {'label':'owner_name', 'type': 'text'},
            {'label':'owner_address', 'type': 'text'},
            {'label':'owner_telephone_number', 'type': 'text'},
            {'label':'uid', 'type': 'text'}
            ]


class UserVerification(AbstractVerificationEntry):
    name = models.CharField(max_length=128)
    address = models.CharField(max_length=128)
    telephone_number = models.CharField(max_length=16)
    date_of_birth = models.DateField()
    receiving_wallet = models.ForeignKey(
        Wallet, blank=True, null=True, on_delete=models.SET_NULL, related_name='user_claims')

    @staticmethod
    def to_verification_input_dict():
        return [
            {'label':'name', 'type': 'text'},
            {'label':'address', 'type': 'text'},
            {'label':'telephone_number', 'type': 'text'},
            {'label':'date_of_birth', 'type': 'date'},
            ]
