from django.core.exceptions import ValidationError
from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.wallet.models import (WALLET_STATES, MetaTransaction, Transaction,
                                Wallet)


@receiver(pre_save, sender=Transaction, dispatch_uid='custom_transaction_validation')
def custom_transaction_validation(sender, instance, **kwargs):
    if instance.amount <= 0:
        raise ValidationError("Amount must be > 0")
    if instance.is_mint_transaction and not instance.to_wallet.currency.allow_minting:
        raise ValidationError(
            "Currency must allow minting if you want to mint")
    # The notification of the wallet is handled inside the utils.create_claim_transaction if it's not a MetaTransaction


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

    instance.to_wallet.notify_owner_receiving_money(
        instance.from_wallet, instance.amount)
    instance.to_wallet.notify_transfer_successful(
        instance.to_wallet, instance.amount)


@receiver(pre_save, sender=Wallet, dispatch_uid='pre_save_signal_wallet')
def pre_save_signal_wallet(sender, instance, **kwargs):
    if instance.uuid is not None:
        try:
            previous = Wallet.objects.get(uuid=instance.uuid)

            if instance.state != previous.state and instance.state == WALLET_STATES.VERIFIED:
                instance.notify_owner_verified()
        except Wallet.DoesNotExist:
            pass
