import base64
import secrets
import string
from enum import Enum
from urllib.parse import urlencode

import pysodium
import pytezos
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max, Q, Sum
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from fcm_django.models import FCMDevice
from pytezos.crypto.key import Key
from schwifty import IBAN

from apps.currency.mixins import CurrencyOwnedMixin
from apps.wallet.utils import create_message
from project.mixins import UUIDModel


class WALLET_STATES(Enum):
    UNVERIFIED = 0
    PENDING = 1
    VERIFIED = 2
    DEACTIVATED = 3


class WALLET_CATEGORIES(Enum):
    CONSUMER = 0
    COMPANY = 1
    OWNER = 2


WALLET_STATE_CHOICES = (
    (WALLET_STATES.UNVERIFIED.value, _("Unverified")),
    (WALLET_STATES.PENDING.value, _("Pending")),
    (WALLET_STATES.VERIFIED.value, _("Verified")),
    (WALLET_STATES.DEACTIVATED.value, _("Deactivated")),
)

WALLET_CATEGORY_CHOICES = (
    (WALLET_CATEGORIES.CONSUMER.value, _("Consumer")),
    (WALLET_CATEGORIES.COMPANY.value, _("Company")),
    (WALLET_CATEGORIES.OWNER.value, _("Owner")),
)


class Wallet(CurrencyOwnedMixin):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        related_name="wallets",
    )
    wallet_id = models.CharField(
        _("Wallet Id"), unique=True, blank=True, editable=False, max_length=128
    )
    public_key = models.CharField(
        _("Publickey"), unique=True, blank=True, editable=True, max_length=60
    )  # encoded public_key
    category = models.IntegerField(
        _("Category"),
        default=WALLET_CATEGORIES.CONSUMER.value,
        choices=WALLET_CATEGORY_CHOICES,
    )
    state = models.IntegerField(
        _("State"), default=WALLET_STATES.UNVERIFIED.value, choices=WALLET_STATE_CHOICES
    )

    @property
    def address(self):
        return Key.from_encoded_key(self.public_key).public_key_hash()

    @property
    def balance(self):
        return (
            self.to_transactions.aggregate(Sum("amount")).get("amount__sum") or 0
        ) - (self.from_transactions.aggregate(Sum("amount")).get("amount__sum") or 0)

    @property
    def from_metatransactions(self):
        return MetaTransaction.objects.filter(from_wallet=self)

    @property
    def nonce(self):
        # filter out amount==0
        transactions = self.from_metatransactions.filter(
            from_public_key=self.public_key, amount__gt=0
        )
        if transactions.count() == 0:
            return 0
        else:
            return transactions.aggregate(Max("nonce"))["nonce__max"]

    @property
    def is_in_public_key_transfer(self):
        return self.transfer_requests.filter(state=2).exists()

    def __str__(self):
        return "{} - {}".format(self.wallet_id, self.currency)

    @staticmethod
    def generate_wallet_id():
        characters = get_random_string(2, string.ascii_uppercase)
        digits = str(secrets.randbelow(999999)).zfill(6)
        return characters + digits

    def notify_owner_receiving_money(self, from_wallet_id, amount):
        # TODO: multi language support?
        self.__notify_owner_devices(
            f"Sie haben {amount/pow(10,self.currency.decimals)} CHF von {from_wallet_id} erhalten"
        )

    def notify_transfer_successful(self, to_wallet_id, amount):
        self.__notify_owner_devices(
            f"Sie haben {amount/pow(10,self.currency.decimals)} CHF an {to_wallet_id} gesendet"
        )

    def notify_owner_verified(self):
        self.__notify_owner_devices(f"Wallet {self.wallet_id} wurde verifiziert")

    def notify_owner_transfer_request_done(self):
        self.__notify_owner_devices(
            f"PublicKeyRequest vollzogen für {self.wallet_id}", data=self.wallet_id
        )

    def __notify_owner_devices(self, message, data=None):
        devices = FCMDevice.objects.filter(user=self.owner)
        devices.send_message(
            title=settings.PUSH_NOTIFICATION_TITLE, body=message, data=data
        )

    def clean(self, *args, **kwargs):
        super(Wallet, self).clean(*args, **kwargs)
        errors = {}
        # TODO: more to clean?
        try:
            self.address
        except:
            errors["public_key"] = ValidationError(
                _("Public key is not in valid format")
            )

        if len(errors) > 0:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.category == WALLET_CATEGORIES.CONSUMER.value and self._state.adding:
            self.state = WALLET_STATES.VERIFIED.value
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["created_at"]


class OwnerWallet(Wallet):
    private_key = models.CharField(
        _("Privatekey"), unique=True, blank=True, editable=False, max_length=128
    )

    def save(self, *args, **kwargs):
        self.state = WALLET_STATES.VERIFIED.value
        self.category = WALLET_CATEGORIES.OWNER.value
        super(OwnerWallet, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if self.private_key is None or len(self.private_key) <= 0:
            key = Key.generate()
            self.private_key = key.secret_key()
            self.public_key = key.public_key()
        super(Wallet, self).clean(*args, **kwargs)


class PaperWallet(Wallet):
    user_verification = models.ForeignKey(
        "verification.UserVerification",
        null=True,
        on_delete=models.DO_NOTHING,
        blank=True,
    )
    private_key = models.CharField(unique=True, max_length=128)

    @property
    def can_be_used_for_verification(self):
        if self.category == WALLET_CATEGORIES.COMPANY.value:
            return (
                self.from_transactions.count() == 0
                and self.to_transactions.count() == 0
                and self.balance == 0
            )

        return (
            self.from_transactions.count() == 0
            and self.to_transactions.count() == 1
            and self.balance == self.currency.starting_capital
        )

    @staticmethod
    def generate_new_wallet(
        currency,
        place_of_origin,
        user_verification,
        category=WALLET_CATEGORIES.CONSUMER.value,
        state=WALLET_STATES.VERIFIED.value,
    ):
        with transaction.atomic():
            while True:
                wallet_id = Wallet.generate_wallet_id()
                if Wallet.objects.filter(wallet_id=wallet_id).exists():
                    continue
                else:
                    key = Key.generate()
                    private_key = key.secret_key()
                    public_key = key.public_key()

                    from apps.profiles.models import UserProfile

                    username = slugify(
                        "%s %s %s"
                        % (
                            user_verification.first_name,
                            user_verification.last_name,
                            get_random_string(10),
                        )
                    )
                    while get_user_model().objects.filter(username=username).exists():
                        username = slugify(
                            "%s %s %s"
                            % (
                                user_verification.first_name,
                                user_verification.last_name,
                                get_random_string(10),
                            )
                        )

                    user = get_user_model().objects.create(
                        username=username,
                        password=get_user_model().objects.make_random_password(),
                    )

                    from apps.verification.models import VERIFICATION_STATES

                    # if we do not change the state here and save before we save the new user profile, then we trigger an SMS verification
                    user_verification.state = VERIFICATION_STATES.CLAIMED.value
                    user_verification.save()

                    profile = UserProfile(
                        owner=user,
                        first_name=user_verification.first_name,
                        last_name=user_verification.last_name,
                        address_street=user_verification.address_street,
                        address_town=user_verification.address_town,
                        address_postal_code=user_verification.address_postal_code,
                        telephone_number="+417",
                        date_of_birth=user_verification.date_of_birth,
                        place_of_origin=place_of_origin.place_of_origin,
                    )

                    paper_wallet = PaperWallet.objects.create(
                        user_verification=user_verification,
                        owner=user,
                        wallet_id=wallet_id,
                        private_key=private_key,
                        public_key=public_key,
                        currency=currency,
                        state=WALLET_STATES.VERIFIED.value,
                        category=category,
                    )

                    profile.wallet = paper_wallet
                    profile.save()

                    user_verification.user_profile = profile
                    user_verification.save()

                    return paper_wallet

    def generate_deeplink(self):
        encryption_key = bytes.fromhex(settings.ENCRYPTION_KEY)
        nonce = pysodium.randombytes(pysodium.crypto_secretbox_NONCEBYTES)
        pk = pysodium.crypto_aead_xchacha20poly1305_ietf_encrypt(
            self.private_key.encode("UTF-8"), None, nonce, encryption_key
        )
        # TODO: never used?!?
        # decrypted_pk = pysodium.crypto_aead_xchacha20poly1305_ietf_decrypt(
        #     pk, None, nonce, encryption_key)

        payload = {
            "nonce": base64.b64encode(nonce),
            "id": self.wallet_id,
            "pk": base64.b64encode(pk),
        }

        return (
            "https://ecoo.page.link/?"
            + urlencode(
                {
                    "link": "{}wallet/?{}".format(
                        settings.DEEPLINK_BASE_URL, urlencode(payload)
                    )
                }
            )
            + "&apn=ch.ecoupon.mobile.android&ibi=ch.ecoupon.mobile"
        )

    def save(self, *args, **kwargs):
        self.state = WALLET_STATES.VERIFIED.value
        super(PaperWallet, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Paper wallet")
        verbose_name_plural = _("Paper wallets")


class TRANSACTION_STATES(Enum):
    OPEN = 1
    PENDING = 2
    DONE = 3
    FAILED = 4


TRANSACTION_STATE_CHOICES = (
    (TRANSACTION_STATES.OPEN.value, "Open"),
    (TRANSACTION_STATES.PENDING.value, "Pending"),
    (TRANSACTION_STATES.DONE.value, "Done"),
    (TRANSACTION_STATES.FAILED.value, "Failed"),
)


class Transaction(UUIDModel):
    from_wallet = models.ForeignKey(
        Wallet,
        verbose_name=_("From Wallet"),
        on_delete=models.DO_NOTHING,
        related_name="from_transactions",
        blank=True,
        null=True,
    )
    to_wallet = models.ForeignKey(
        Wallet,
        verbose_name=_("To Wallet"),
        on_delete=models.DO_NOTHING,
        related_name="to_transactions",
    )
    amount = models.IntegerField(
        verbose_name=_("Amount"),
    )

    state = models.IntegerField(
        verbose_name=_("State"),
        choices=TRANSACTION_STATE_CHOICES,
        default=TRANSACTION_STATES.OPEN.value,
    )

    submitted_to_chain_at = models.DateTimeField(
        verbose_name=_("Submitted to chain"), null=True, blank=True, editable=False
    )

    operation_hash = models.CharField(
        verbose_name=_("Operation hash"), max_length=128, blank=True, editable=False
    )

    notes = models.TextField(verbose_name=_("Notes"), blank=True)

    user_notes = models.TextField(verbose_name=_("User notes"), blank=True)

    def __str__(self):
        if self.from_wallet:
            return "{} -{}-> {}".format(
                self.from_wallet.wallet_id, self.amount, self.to_wallet.wallet_id
            )
        else:
            return "-{}-> {}".format(self.amount, self.to_wallet.wallet_id)

    @property
    def is_cashout_transaction(self) -> bool:
        return self.to_wallet == self.to_wallet.currency.cashout_wallet

    @property
    def is_mint_transaction(self):
        return self.from_wallet is None

    @property
    def is_verification_transaction(self):
        # TODO: is this correct?

        from_wallet = self.from_wallet

        if from_wallet is None:
            return False

        if PaperWallet.objects.filter(wallet_id=from_wallet.wallet_id).count() == 0:
            return False

        if (
            from_wallet.from_transactions.count() == 0
            and from_wallet.balance == self.amount
            and not self.pk
        ):
            return True

        if (
            from_wallet.from_transactions.count() == 1
            and from_wallet.balance == 0
            and self.pk
        ):
            return True
        return False

    @property
    def tag(self):
        if (
            self.from_wallet
            and self.from_wallet == self.from_wallet.currency.owner_wallet
        ):
            return "from_owner"

        if self.to_wallet == self.to_wallet.currency.owner_wallet:
            return "to_owner"

        return ""

    @staticmethod
    def get_belonging_to_user(user):
        belonging_wallets = user.wallets.all()
        return Transaction.objects.filter(
            Q(from_wallet__in=belonging_wallets) | Q(to_wallet__in=belonging_wallets)
        )

    def clean(self, *args, **kwargs):
        errors = {}

        if hasattr(self, "to_wallet"):
            if self.to_wallet.transfer_requests.exclude(
                state=TRANSACTION_STATES.DONE.value
            ).exists():
                errors["to_wallet"] = ValidationError(
                    _(
                        "Wallet transfer ongoing for destination wallet, cannot send funds to this wallet at the moment."
                    )
                )
            if self.is_mint_transaction and not self.to_wallet.currency.allow_minting:
                errors["to_wallet"] = ValidationError(
                    _("Currency must allow minting if you want to mint")
                )

        if self.amount is not None and self.amount < 0:
            errors["amount"] = ValidationError(_("Amount must be >= 0"))

        if self.amount == 0:
            self.state = TRANSACTION_STATES.DONE.value

        if not self.is_mint_transaction:
            if hasattr(self, "from_wallet"):
                if self.amount and self.from_wallet.balance < self.amount:
                    errors["from_wallet"] = ValidationError(
                        _("Balance of from_wallet must be greater than amount")
                    )

                if (
                    hasattr(self, "to_wallet")
                    and self.from_wallet.currency != self.to_wallet.currency
                ):
                    errors["from_wallet"] = ValidationError(
                        _('"From wallet" and "to wallet" need to use same currency')
                    )
                    errors["to_wallet"] = ValidationError(
                        _('"From wallet" and "to wallet" need to use same currency')
                    )

                if self.from_wallet.transfer_requests.exclude(
                    state=TRANSACTION_STATES.DONE.value
                ).exists():
                    errors["from_wallet"] = ValidationError(
                        _(
                            "Wallet transfer ongoing for source wallet, cannot send funds from this wallet at the moment."
                        )
                    )
                if self.from_wallet.state != WALLET_STATES.VERIFIED.value:
                    errors["from_wallet"] = ValidationError(
                        _("Only verified addresses can send money")
                    )

                if self.is_verification_transaction and not self.pk:
                    # check max_claim count if transaction would be created
                    claim_count = sum(
                        [
                            1
                            for tx in Transaction.objects.filter(
                                to_wallet=self.to_wallet
                            )
                            if tx.is_verification_transaction
                        ]
                    )
                    if claim_count > self.to_wallet.currency.max_claims:
                        raise ValidationError(_("Claim maximum reached"))

                if self.to_wallet.state != WALLET_STATES.VERIFIED.value:
                    # wallet is not verified
                    from apps.verification.models import VERIFICATION_STATES

                    if self.is_verification_transaction:

                        profile = (
                            self.to_wallet.user_profiles.first()
                            if self.to_wallet.category
                            == WALLET_CATEGORIES.CONSUMER.value
                            else self.to_wallet.company_profiles.first()
                        )
                        if (
                            profile
                            and profile.sms_pin_verifications
                            and profile.sms_pin_verifications.count() > 0
                            and profile.sms_pin_verifications.first().state
                            == VERIFICATION_STATES.CLAIMED.value
                        ) or not self.to_wallet.currency.needs_sms_verification:
                            self.to_wallet.state = WALLET_STATES.VERIFIED.value
                            self.to_wallet.save()

                        else:
                            errors["to_wallet"] = ValidationError(
                                "To wallet needs sms verification before a 'verification transaction' can be created"
                            )

        if len(errors) > 0:
            raise ValidationError(errors)
        super(Transaction, self).clean(*args, **kwargs)

    @property
    def currency_amount(self):
        if self.from_wallet:
            decimals = self.from_wallet.currency.decimals
        elif self.to_wallet:
            decimals = self.to_wallet.currency.decimals
        else:
            decimals = 2
        return self.amount / 10 ** decimals

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class MetaTransaction(Transaction):
    nonce = models.IntegerField()
    signature = models.CharField(max_length=128, unique=True)
    from_public_key = models.CharField(
        _("Publickey"), blank=True, editable=False, max_length=60
    )

    def to_meta_transaction_dictionary(self):
        return {
            "from_public_key": self.from_wallet.public_key,
            "signature": self.signature,
            "nonce": self.nonce,
            "txs": [
                {
                    "to_": self.to_wallet.address,
                    "amount": self.amount,
                    "token_id": self.from_wallet.currency.token_id,
                }
            ],
        }

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        errors = {}

        if self.is_mint_transaction:
            errors["from_wallet"] = ValidationError(
                _("Metatransaction always must have from")
            )
        if not self.nonce or self.nonce <= 0:
            errors["nonce"] = ValidationError(_("Nonce must be > 0"))

        if hasattr(self, "from_wallet"):

            if self.from_wallet and self.nonce != self.from_wallet.nonce + 1:
                errors["nonce"] = ValidationError(
                    _(
                        "Nonce must be 1 higher than from_wallet's last meta transaction nonce"
                    )
                )

        try:
            message = create_message(
                self.from_wallet,
                self.to_wallet,
                self.nonce,
                self.from_wallet.currency.token_id,
                self.amount,
            )
        except:
            pass
        if self.from_wallet and self.to_wallet:
            self.from_public_key = self.from_wallet.public_key
            key = pytezos.Key.from_encoded_key(self.from_public_key)
            try:
                key.verify(self.signature, message)
            except ValueError:
                errors["signature"] = ValidationError(_("Signature is invalid"))

        if len(errors) > 0:
            raise ValidationError(errors)

        super(MetaTransaction, self).clean(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Meta transaction")
        verbose_name_plural = _("Meta transactions")
        unique_together = ("nonce", "from_public_key")


class WalletPublicKeyTransferRequest(UUIDModel):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.DO_NOTHING, related_name="transfer_requests"
    )
    old_public_key = models.CharField(max_length=60, blank=True)
    new_public_key = models.CharField(max_length=60)
    state = models.IntegerField(
        choices=TRANSACTION_STATE_CHOICES, default=TRANSACTION_STATES.OPEN.value
    )

    submitted_to_chain_at = models.DateTimeField(null=True, blank=True)
    operation_hash = models.CharField(max_length=128, blank=True)

    notes = models.TextField(blank=True, editable=False)

    class Meta:
        ordering = ["-created_at"]


class CashOutRequest(UUIDModel):
    transaction = models.OneToOneField(
        Transaction,
        verbose_name=_("Transaction"),
        on_delete=models.DO_NOTHING,
        related_name="cash_out_requests",
        unique=True,
    )
    state = models.IntegerField(
        verbose_name=_("State"),
        choices=TRANSACTION_STATE_CHOICES,
        default=TRANSACTION_STATES.OPEN.value,
    )
    beneficiary_name = models.CharField(
        verbose_name=_("Beneficiary name"),
        max_length=255,
    )
    beneficiary_iban = models.CharField(
        verbose_name=_("IBAN"),
        max_length=255,
    )

    def clean(self, *args, **kwargs):
        errors = {}
        try:
            IBAN(self.beneficiary_iban)
        except:
            errors["beneficiary_iban"] = ValidationError(_("Iban is incorrect"))

        if hasattr(self, "to_wallet"):
            if (
                self.transaction.to_wallet.uuid
                != self.transaction.to_wallet.currency.cashout_wallet.uuid
            ):
                errors["to_wallet"] = ValidationError(
                    _(
                        "Cash out only possible with transactions going to the owner wallet of the currency"
                    )
                )

        # if self.transaction.from_wallet.category != WALLET_CATEGORIES.COMPANY.value:
        #     errors['from_wallet'] = ValidationError(
        #         _('Cash out only possible from a company wallet'))

        if len(errors) > 0:
            raise ValidationError(errors)

        super(CashOutRequest, self).clean(*args, **kwargs)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Cash out request")
        verbose_name_plural = _("Cash out requests")
