import random
import string
from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Q, Sum
from django.db.models.signals import pre_save
from django.utils.crypto import get_random_string
from pytezos.crypto import Key

from apps.currency.mixins import CurrencyOwnedMixin
from project.mixins import UUIDModel


class Company(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=32)

    class Meta:
        ordering = ['created_at']


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

    @property
    def is_in_public_key_transfer(self):
        return self.transfer_requests.filter(state=2).exists()

    @property
    def claim_count(self):
        from apps.verification.models import VERIFICATION_STATES
        return self.company_claims.filter(state=VERIFICATION_STATES.CLAIMED.value).count() + self.user_claims.filter(state=VERIFICATION_STATES.CLAIMED.value).count()

    def __str__(self):
        return self.wallet_id

    @staticmethod
    def generate_wallet_id():
        characters = get_random_string(2, string.ascii_uppercase)
        digits = str(random.randint(0, 999999)).zfill(6)
        return characters + digits

    class Meta:
        ordering = ['created_at']


class TRANSACTION_STATES(Enum):
    OPEN = 1
    PENDING = 2
    DONE = 3
    FAILED = 4


TRANSACTION_STATE_CHOICES = (
    (TRANSACTION_STATES.OPEN.value, 'Open'),
    (TRANSACTION_STATES.PENDING.value, 'Pending'),
    (TRANSACTION_STATES.DONE.value, 'Done'),
    (TRANSACTION_STATES.FAILED.value, 'Failed'),
)


class WalletPublicKeyTransferRequest(UUIDModel):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='transfer_requests')
    old_public_key = models.CharField(max_length=60, blank=True)
    new_public_key = models.CharField(max_length=60)
    state = models.IntegerField(choices=TRANSACTION_STATE_CHOICES, default=1)

    submitted_to_chain_at = models.DateTimeField(null=True, blank=True)
    operation_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ['created_at']


class Transaction(UUIDModel):
    from_wallet = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='from_transactions', null=True)
    to_wallet = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='to_transactions')
    amount = models.IntegerField()

    state = models.IntegerField(choices=TRANSACTION_STATE_CHOICES, default=1)

    created = models.DateTimeField(auto_now_add=True)
    submitted_to_chain_at = models.DateTimeField(null=True, blank=True)

    operation_hash = models.CharField(max_length=128, blank=True)

    @property
    def is_mint_transaction(self):
        return self.from_wallet == None

    @property
    def tag(self):
        if self.from_wallet and self.from_wallet == self.from_wallet.currency.owner_wallet:
            return 'from_owner'

        if self.to_wallet == self.to_wallet.currency.owner_wallet:
            return 'to_owner'

        return ''

    @staticmethod
    def get_belonging_to_user(user):
        belonging_wallets = user.wallets.all()
        return Transaction.objects.filter(Q(from_wallet__in=belonging_wallets) | Q(to_wallet__in=belonging_wallets))

    class Meta:
        ordering = ['created_at']


class MetaTransaction(Transaction):
    nonce = models.IntegerField()
    signature = models.CharField(max_length=128)

    def to_meta_transaction_dictionary(self):
        return {
            'from_public_key': self.from_wallet.public_key,
            'signature': self.signature,
            'nonce': self.nonce,
            'txs': [
                {'to_': self.to_wallet.address, 'amount': self.amount,
                    'token_id': self.from_wallet.currency.token_id}
            ]
        }

    class Meta:
        ordering = ['created_at']
