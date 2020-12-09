import datetime

from django.core.management.base import BaseCommand, CommandError

from apps.wallet.utils import sync_to_blockchain, check_sync_state


class Command(BaseCommand):
    help = 'Syncs the database with the blockchain'

    def handle(self, *args, **options):
        sync_to_blockchain(is_dry_run=False)
        check_sync_state()
