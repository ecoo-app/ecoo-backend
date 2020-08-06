import datetime

from django.core.management.base import BaseCommand, CommandError

from apps.wallet.utils import publish_open_meta_transactions_to_chain, publish_open_mint_transactions_to_chain, publish_open_transfer_transactions_to_chain, publish_wallet_recovery_transfer_balance


class Command(BaseCommand):
    help = 'Syncs the database with the blockchain'

    def handle(self, *args, **options):
        publish_open_mint_transactions_to_chain()
        publish_open_transfer_transactions_to_chain()
        publish_open_meta_transactions_to_chain()
        publish_wallet_recovery_transfer_balance()
