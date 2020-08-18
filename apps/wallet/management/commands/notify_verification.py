import datetime

from django.core.management.base import BaseCommand, CommandError
from fcm_django.models import FCMDevice

from apps.wallet.models import WALLET_STATES, Wallet
from django.conf import settings


class Command(BaseCommand):
    help = 'Notifies all wallet users which have not verified yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            default=5,
            type=int
        )

    def handle(self, *args, **options):
        delta = datetime.timedelta(days=options['days'])
        today = datetime.datetime.now()

        date_of_interest = (today - delta).date()

        wallets_to_notify = Wallet.objects.filter(
            created_at__date=date_of_interest, state=WALLET_STATES.UNVERIFIED.value)

        user_uuids_to_notify = list(set(wallets_to_notify.values_list('owner')))

        devices = FCMDevice.objects.filter(user__in=user_uuids_to_notify)

        self.stdout.write(f'Notifying {len(devices)} potential devices')
        devices.send_message(title=settings.PUSH_NOTIFICATION_TITLE, body="Bitte verifizieren Sie ihren Account")
