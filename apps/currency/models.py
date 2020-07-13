from enum import Enum

from django.db import models

from project.mixins import UUIDModel


class Currency(UUIDModel):
    name = models.CharField(max_length=32)

    # TODO: additional fields?
    def __str__(self):
        return self.name


class VERIFICATION_INPUT_STATES(Enum):
    TEXT = 1
    BOOLEAN = 2
    NUMBER = 3
    DATE = 4

VERIFICATION_INPUT_CHOICES =  (
    (VERIFICATION_INPUT_STATES.TEXT.value, 'Text'),
    (VERIFICATION_INPUT_STATES.BOOLEAN.value, 'Boolean'),
    (VERIFICATION_INPUT_STATES.NUMBER.value, 'Date'),
    (VERIFICATION_INPUT_STATES.DATE.value, 'Number'),
)

class VerificationInput(UUIDModel):
    currency = models.ForeignKey(
        Currency, on_delete=models.SET_NULL, null=True,)

    label = models.CharField(max_length=32)
    data_type = models.IntegerField(default=0, choices=VERIFICATION_INPUT_CHOICES)
    # -> Set to verified if ok (on post request); cannot claim until verified
