from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.wallet.models import WalletPublicKeyTransferRequest, OwnerWallet, Wallet, CashOutRequest, MetaTransaction, Transaction, WALLET_CATEGORIES, WALLET_STATES
from apps.wallet.utils import sync_to_blockchain
from django_simple_task import defer


@receiver(pre_save, sender=Transaction, dispatch_uid='custom_transaction_validation')
def custom_transaction_validation(sender, instance, **kwargs):
    instance.full_clean()


@receiver(pre_save, sender=MetaTransaction, dispatch_uid='custom_meta_transaction_validation')
def custom_meta_transaction_validation(sender, instance, **kwargs):
    instance.full_clean()

    instance.to_wallet.notify_owner_receiving_money(
        instance.from_wallet, instance.amount)
    instance.from_wallet.notify_transfer_successful(
        instance.to_wallet, instance.amount)


@receiver(pre_save, sender=Wallet, dispatch_uid='pre_save_signal_wallet')
@receiver(pre_save, sender=OwnerWallet, dispatch_uid='pre_save_signal_owner_wallet')
def pre_save_signal_wallet(sender, instance, **kwargs):
    instance.full_clean()

    if instance.wallet_id is None or len(instance.wallet_id) <= 0:
        instance.wallet_id = Wallet.generate_wallet_id()
        while Wallet.objects.filter(wallet_id=instance.wallet_id).exists():
            instance.wallet_id = Wallet.generate_wallet_id()
    if instance.uuid is not None:
        try:
            previous = Wallet.objects.get(uuid=instance.uuid)
            if instance.state != previous.state and instance.state == WALLET_STATES.VERIFIED:
                instance.notify_owner_verified()
        except Wallet.DoesNotExist:
            pass


@receiver(pre_save, sender=CashOutRequest, dispatch_uid='custom_cash_out_request_validation')
def custom_cash_out_request_validation(sender, instance, **kwargs):
    instance.full_clean()


@receiver(post_save, sender=WalletPublicKeyTransferRequest, dispatch_uid='async_sync_to_blockchain_after_wallet_public_key_transfer')
def async_sync_to_blockchain_after_wallet_public_key_transfer(sender, instance, created, **kwargs):
    if created:
        defer(lambda: sync_to_blockchain(is_dry_run=False))
