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
from fcm_django.models import FCMDevice
from pytezos.crypto import Key
import pytezos

from apps.currency.mixins import CurrencyOwnedMixin
from project.mixins import UUIDModel
from django.utils.translation import ugettext_lazy as _
from apps.wallet.utils import create_message
from schwifty import IBAN


class WALLET_STATES(Enum):
    UNVERIFIED = 0
    PENDING = 1
    VERIFIED = 2


class WALLET_CATEGORIES(Enum):
    CONSUMER = 0
    COMPANY = 1
    OWNER = 2


WALLET_STATE_CHOICES = (
    (WALLET_STATES.UNVERIFIED.value, _('Unverified')),
    (WALLET_STATES.PENDING.value, _('Pending')),
    (WALLET_STATES.VERIFIED.value, _('Verified')),
)

WALLET_CATEGORY_CHOICES = (
    (WALLET_CATEGORIES.CONSUMER.value, _('Consumer')),
    (WALLET_CATEGORIES.COMPANY.value, _('Company')),
    (WALLET_CATEGORIES.OWNER.value, _('Owner')),
)


class Wallet(CurrencyOwnedMixin):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True,
                              null=True, on_delete=models.DO_NOTHING, related_name='wallets')
    wallet_id = models.CharField(
        _('Wallet Id'), unique=True, blank=True, editable=False, max_length=128)
    public_key = models.CharField(
        _('Publickey'), unique=True, max_length=60)  # encoded public_key
    category = models.IntegerField(
        _('Category'), default=WALLET_CATEGORIES.CONSUMER.value, choices=WALLET_CATEGORY_CHOICES)
    state = models.IntegerField(
        _('State'), default=WALLET_STATES.UNVERIFIED.value, choices=WALLET_STATE_CHOICES)

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

    def __str__(self):
        return '{} - {}'.format(self.wallet_id, self.currency)

    @staticmethod
    def generate_wallet_id():
        characters = get_random_string(2, string.ascii_uppercase)
        digits = str(secrets.randbelow(999999)).zfill(6)
        return characters + digits

    def notify_owner_receiving_money(self, from_wallet_id, amount):
        # TODO: multi language support?
        self.__notify_owner_devices(
            f'Sie haben {amount/pow(10,self.currency.decimals)} CHF von {from_wallet_id} erhalten')

    def notify_transfer_successful(self, to_wallet_id, amount):
        self.__notify_owner_devices(
            f'Sie haben {amount/pow(10,self.currency.decimals)} CHF an {to_wallet_id} gesendet')

    def notify_owner_verified(self):
        self.__notify_owner_devices(
            f'Wallet {self.wallet_id} wurde verifiziert')

    def __notify_owner_devices(self, message):
        devices = FCMDevice.objects.filter(user=self.owner)
        devices.send_message(
            title=settings.PUSH_NOTIFICATION_TITLE, body=message)

    def clean(self, *args, **kwargs):
        super(Wallet, self).clean(*args, **kwargs)
        try:
            self.address
        except:
            raise ValidationError(_('Public key is not in valid format'))

    class Meta:
        ordering = ['created_at']


class OwnerWallet(Wallet):
    private_key = models.CharField(
        _('Privatekey'), unique=True, max_length=128)

    def save(self, *args, **kwargs):
        self.state = WALLET_CATEGORIES.OWNER.value
        super(OwnerWallet, self).save(*args, **kwargs)


class PaperWallet(Wallet):
    user_verification = models.ForeignKey(
        'verification.UserVerification', null=True, on_delete=models.DO_NOTHING, )
    private_key = models.CharField(unique=True, max_length=128)

    def save(self, *args, **kwargs):
        self.state = WALLET_CATEGORIES.OWNER.value
        super(PaperWallet, self).save(*args, **kwargs)


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
    from_wallet = models.ForeignKey(Wallet, verbose_name=_(
        'From Wallet'), on_delete=models.DO_NOTHING, related_name='from_transactions', blank=True, null=True)
    to_wallet = models.ForeignKey(Wallet, verbose_name=_(
        'To Wallet'), on_delete=models.DO_NOTHING, related_name='to_transactions')
    amount = models.IntegerField(verbose_name=_('Amount'),)

    state = models.IntegerField(verbose_name=_(
        'State'), choices=TRANSACTION_STATE_CHOICES, default=TRANSACTION_STATES.OPEN.value)

    submitted_to_chain_at = models.DateTimeField(verbose_name=_(
        'Submitted to chain'), null=True, blank=True, editable=False)

    operation_hash = models.CharField(verbose_name=_(
        'Operation hash'), max_length=128, blank=True, editable=False)

    notes = models.TextField(verbose_name=_(
        'Notes'), blank=True, editable=False)

    def __str__(self):
        if self.from_wallet:
            return "{} -{}-> {}".format(self.from_wallet.wallet_id, self.amount, self.to_wallet.wallet_id)
        else:
            return "-{}-> {}".format(self.amount, self.to_wallet.wallet_id)

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

    def clean(self, *args, **kwargs):

        if self.to_wallet.transfer_requests.exclude(state=TRANSACTION_STATES.DONE.value).exists():
            raise ValidationError(
                _('Wallet transfer ongoing for destination wallet, cannot send funds to this wallet at the moment.'))
        if self.amount <= 0:
            raise ValidationError(_('Amount must be > 0'))
        if self.is_mint_transaction and not self.to_wallet.currency.allow_minting:
            raise ValidationError(
                _('Currency must allow minting if you want to mint'))

        if not self.is_mint_transaction:
            if self.from_wallet.balance < self.amount:
                raise ValidationError(
                    _('Balance of from_wallet must be greater than amount'))
            if self.from_wallet.currency != self.to_wallet.currency:
                raise ValidationError(
                    _('"From wallet" and "to wallet" need to use same currency'))
            if self.from_wallet.transfer_requests.exclude(state=TRANSACTION_STATES.DONE.value).exists():
                raise ValidationError(
                    _('Wallet transfer ongoing for source wallet, cannot send funds from this wallet at the moment.'))
            if self.from_wallet.state != WALLET_STATES.VERIFIED.value:
                raise ValidationError(
                    _('Only verified addresses can send money'))

        super(Transaction, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')


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

    def clean(self, *args, **kwargs):
        if self.is_mint_transaction:
            raise ValidationError(_('Metatransaction always must have from'))
        if not self.nonce or self.nonce <= 0:
            raise ValidationError(_('Nonce must be > 0'))
        if self.nonce <= (MetaTransaction.objects.filter(from_wallet=self.from_wallet).aggregate(Max('nonce'))['nonce__max'] or 0):
            raise ValidationError(
                _('Nonce must be higher than from_wallet\'s last meta transaction'))
        if self.from_wallet.currency != self.to_wallet.currency:
            raise ValidationError(
                _('"From wallet" and "to wallet" need to use same currency'))

        message = create_message(self.from_wallet, self.to_wallet,
                                 self.nonce, self.from_wallet.currency.token_id, self.amount)
        key = pytezos.Key.from_encoded_key(self.from_wallet.public_key)
        try:
            key.verify(self.signature, message)
        except ValueError:
            raise ValidationError(_('Signature is invalid'))

        super(MetaTransaction, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Meta transaction')
        verbose_name_plural = _('Meta transactions')


class WalletPublicKeyTransferRequest(UUIDModel):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name='transfer_requests')
    old_public_key = models.CharField(max_length=60, blank=True)
    new_public_key = models.CharField(max_length=60)
    state = models.IntegerField(
        choices=TRANSACTION_STATE_CHOICES, default=TRANSACTION_STATES.OPEN.value)

    submitted_to_chain_at = models.DateTimeField(null=True, blank=True)
    operation_hash = models.CharField(max_length=128, blank=True)

    notes = models.TextField(blank=True, editable=False)

    class Meta:
        ordering = ['created_at']


class CashOutRequest(UUIDModel):
    transaction = models.OneToOneField(Transaction, verbose_name=_(
        'Transaction'), on_delete=models.DO_NOTHING, related_name='cash_out_requests', unique=True)
    state = models.IntegerField(verbose_name=_(
        'State'), choices=TRANSACTION_STATE_CHOICES, default=TRANSACTION_STATES.OPEN.value)
    beneficiary_name = models.CharField(
        verbose_name=_('Beneficiary name'), max_length=255,)
    beneficiary_iban = models.CharField(
        verbose_name=_('IBAN'), max_length=255,)

    def clean(self, *args, **kwargs):
        try:
            IBAN(self.beneficiary_iban)
        except:
            raise ValidationError(_('Iban is incorrect'))
        if self.transaction.to_wallet.uuid != self.transaction.to_wallet.currency.owner_wallet.uuid:
            raise ValidationError(
                _('Cash out only possible with transactions going to the owner wallet of the currency'))

        super(CashOutRequest, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Cash out request')
        verbose_name_plural = _('Cash out requests')
