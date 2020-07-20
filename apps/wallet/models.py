import random
import string
from enum import Enum

from django.db import models
from django.db.models import Q, Sum
from django.utils.crypto import get_random_string

from apps.currency.mixins import CurrencyOwnedMixin
from apps.wallet.utils import getBalanceForWallet
from django.conf import settings
from project.mixins import UUIDModel
from pytezos.crypto import Key


class Company(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=32)


class ClaimableAmount(CurrencyOwnedMixin):
    identifier = models.TextField(blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)


class WALLET_STATES(Enum):
    UNVERIFIED = 0
    PENDING = 1
    VERIFIED = 2


class WALLET_CATEGORIES(Enum):
    CONSUMER = 0
    COMPANY = 1
    OWNER = 2


WALLET_STATE_CHOICES = (
    (WALLET_STATES.UNVERIFIED.value, 'Unverified'),
    (WALLET_STATES.PENDING.value, 'Pending'),
    (WALLET_STATES.VERIFIED.value, 'Verified'),
)

WALLET_CATEGORY_CHOICES = (
    (WALLET_CATEGORIES.CONSUMER.value, 'Consumer'),
    (WALLET_CATEGORIES.COMPANY.value, 'Company'),
    (WALLET_CATEGORIES.OWNER.value, 'Owner'),
)


class Wallet(CurrencyOwnedMixin):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.DO_NOTHING, related_name='wallets')
    company = models.ForeignKey(
        Company, blank=True, null=True, on_delete=models.SET_NULL, related_name='wallets')

    wallet_id = models.CharField(unique=True, max_length=128)
    public_key = models.CharField(
        unique=True, max_length=60)  # encoded public_key

    category = models.IntegerField(
        default=0, choices=WALLET_CATEGORY_CHOICES)
    state = models.IntegerField(default=0, choices=WALLET_STATE_CHOICES)

    @property
    def address(self):
        return Key.from_encoded_key(self.public_key).public_key_hash()

    @property
    def balance(self):
        return (self.to_transactions.aggregate(Sum('amount')).get('amount__sum') or 0) - (self.from_transactions.aggregate(Sum('amount')).get('amount__sum') or 0)

    @property
    def nonce(self):
        return self.from_transactions.count()

    def __str__(self):
        return self.wallet_id

    @staticmethod
    def get_belonging_to_user(user):
        if user.is_superuser:
            return Wallet.objects.all()

        return Wallet.objects.filter(Q(owner=user) | Q(company__owner=user))

    # TODO:  no camelcase in properties, use _, also shouldn't this be generate_wallet_id?
    @staticmethod
    def generate_wallet_id():
        characters = get_random_string(2, string.ascii_uppercase)
        digits = str(random.randint(0, 999999)).zfill(6)
        return characters + digits


class TRANSACTION_STATES(Enum):
    OPEN = 1
    PENDING = 2
    DONE = 3


TRANSACTION_STATE_CHOICES = (
    (TRANSACTION_STATES.OPEN.value, 'Open'),
    (TRANSACTION_STATES.PENDING.value, 'Pending'),
    (TRANSACTION_STATES.DONE.value, 'Done'),
)


class TokenTransaction(UUIDModel):
    # TODO: rename fields to from_wallet etc.
    from_addr = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='from_transactions')
    to_addr = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='to_transactions')
    amount = models.IntegerField()

    state = models.IntegerField(choices=TRANSACTION_STATE_CHOICES, default=1)
    signature = models.CharField(max_length=128, null=True)

    created = models.DateTimeField(auto_now_add=True, null=True)
    submitted_to_chain_at = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def get_belonging_to_user(user):
        belonging_wallets = user.wallets
        return TokenTransaction.objects.filter(Q(from_addr__in=belonging_wallets) | Q(to_addr__in=belonging_wallets))
