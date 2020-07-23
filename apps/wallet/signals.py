from django.core.exceptions import ValidationError
from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.wallet.models import MetaTransaction, Transaction


@receiver(pre_save, sender=Transaction, dispatch_uid='custom_transaction_validation')
def custom_transaction_validation(sender, instance, **kwargs):
    if instance.amount <= 0:
        raise ValidationError("Amount must be > 0")
    if instance.is_mint_transaction and not instance.to_wallet.currency.allow_minting:
        raise ValidationError(
            "Currency must allow minting if you want to mint")
    if not instance.is_mint_transaction:
        if instance.from_wallet.balance < instance.amount:
            raise ValidationError(
                "Balance of from_wallet must be greater than amount")
        if instance.from_wallet.currency != instance.to_wallet.currency:
            raise ValidationError(
                "'From wallet' and 'to wallet' need to use same currency")


@receiver(pre_save, sender=MetaTransaction, dispatch_uid='custom_meta_transaction_validation')
def custom_meta_transaction_validation(sender, instance, **kwargs):
    custom_transaction_validation(sender, instance)
    if instance.is_mint_transaction:
        raise ValidationError("Metatransaction always must have from")
    if not instance.nonce or instance.nonce <= 0:
        raise ValidationError("Nonce must be > 0")
    if instance.nonce <= (MetaTransaction.objects.filter(from_wallet=instance.from_wallet).aggregate(Max('nonce'))['nonce__max'] or 0):
        raise ValidationError(
            "Nonce must be higher than from_wallet's last meta transaction")
