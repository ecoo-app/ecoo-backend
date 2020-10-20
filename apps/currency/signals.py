import pytezos
from django.db import IntegrityError
from django.db.models import Max
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.currency.models import Currency
from apps.wallet.models import OwnerWallet, WALLET_CATEGORIES


@receiver(post_save, sender=Currency, dispatch_uid='currency_create_owner_wallet')
def create_owner_wallet(sender, instance, created, **kwargs):

    if created:
        key = pytezos.crypto.Key.generate()
        private_key = key.secret_key()
        public_key = key.public_key()

        retry = True
        while retry:
            try:
                owner_wallet = OwnerWallet.objects.create(currency=instance, private_key=private_key, wallet_id=OwnerWallet.generate_wallet_id(
                ), public_key=public_key, category=WALLET_CATEGORIES.OWNER.value)
                instance.owner_wallet = owner_wallet
                instance.cashout_wallet = owner_wallet
                instance.save()
                retry = False
            except IntegrityError:
                retry = True
