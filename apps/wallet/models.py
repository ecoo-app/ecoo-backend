import random
import string
from enum import Enum

from django.db import models
from django.db.models import Q, Sum, Max
from django.utils.crypto import get_random_string

from apps.currency.mixins import CurrencyOwnedMixin
from django.conf import settings
from project.mixins import UUIDModel
from pytezos.crypto import Key
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver


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
    def generate_wallet_id():
        characters = get_random_string(2, string.ascii_uppercase)
        digits = str(random.randint(0, 999999)).zfill(6)
        return characters + digits


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


@receiver(pre_save, sender=Transaction, dispatch_uid='custom_transaction_validation')
def custom_transaction_validation(sender, instance, **kwargs):
    if instance.amount <= 0:
        raise ValidationError("Amount must be > 0")
    if instance.is_mint_transaction and not instance.to_wallet.currency.allow_minting:
        raise ValidationError(
            "Currency must allow minting if you want to mint")


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

    @staticmethod
    def get_belonging_to_user(user):
        belonging_wallets = user.wallets.all()
        return MetaTransaction.objects.filter(Q(from_wallet__in=belonging_wallets) | Q(to_wallet__in=belonging_wallets))


@receiver(pre_save, sender=MetaTransaction, dispatch_uid='custom_meta_transaction_validation')
def custom_meta_transaction_validation(sender, instance, **kwargs):
    custom_transaction_validation(sender, instance)
    if instance.is_mint_transaction:
        raise ValidationError("Metatransaction always must have from")
    if not instance.nonce or instance.nonce <= 0:
        raise ValidationError("Nonce must be > 0")
    if instance.from_wallet.balance < instance.amount:
        raise ValidationError(
            "Balance of from_wallet must be greater than amount")
    if instance.nonce <= (MetaTransaction.objects.filter(from_wallet=instance.from_wallet).aggregate(Max('nonce'))['nonce__max'] or 0):
        raise ValidationError(
            "Nonce must be higher than from_wallet's last meta transaction")
    if instance.from_wallet.currency != instance.to_wallet.currency:
        raise ValidationError(
            "'From wallet' and 'to wallet' need to use same currency")
