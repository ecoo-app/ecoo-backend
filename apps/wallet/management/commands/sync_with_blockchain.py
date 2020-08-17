import datetime

from django.core.management.base import BaseCommand, CommandError

from apps.wallet.utils import sync_to_blockchain


class Command(BaseCommand):
    help = 'Syncs the database with the blockchain'

    def handle(self, *args, **options):
        sync_to_blockchain()
