from enum import Enum

from django.db import models

from project.mixins import UUIDModel
from project import settings

# everything belongs to municipality

# class Company(UUIDModel):
    # name

class ClaimableAmount(UUIDModel):
    identifier = models.TextField(blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)


class Wallet(UUIDModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=False, null=True, on_delete=models.DO_NOTHING)
    # company FK
    walletID = models.TextField(unique=True)
    address = models.TextField()
    pub_key = models.TextField()
    # nonce integer


class TRANSACTION_STATES(Enum):
    OPEN = 1
    PENDING = 2
    DONE = 3


PROPOSAL_STATE_CHOICES = (
    (TRANSACTION_STATES.OPEN.value, 'Open'),
    (TRANSACTION_STATES.PENDING.value, 'Pending'),
    (TRANSACTION_STATES.DONE.value, 'Done'),
)


class TokenTransaction(UUIDModel):
    from_addr = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='fromtransaction')
    to_addr = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='totransaction')
    amount = models.FloatField()

    state = models.IntegerField(choices=PROPOSAL_STATE_CHOICES, default=1)

    # nonce = integer -> exposed 
    # signature = char max_length=64

    # increase from wallet nonce