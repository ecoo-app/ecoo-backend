from enum import Enum

from django.db import models

from apps.currency.mixins import CurrencyOwnedMixin
from project.mixins import UUIDModel


class VERIFICATION_STATES(Enum):
    OPEN = 1
    CLAIMED = 2
    REQUESTED = 3


VERIFICATION_STATES_CHOICES = (
    (VERIFICATION_STATES.OPEN.value, 'Open'),
    (VERIFICATION_STATES.CLAIMED.value, 'Claimed'),
    (VERIFICATION_STATES.REQUESTED.value, 'Requested'),
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
