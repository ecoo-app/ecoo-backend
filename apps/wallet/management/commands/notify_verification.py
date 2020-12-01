import datetime

from django.core.management.base import BaseCommand, CommandError
from fcm_django.models import FCMDevice

from apps.wallet.models import WALLET_CATEGORIES, WALLET_STATES, Wallet
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

        consumer_wallet = wallets_to_notify.filter(
            category=WALLET_CATEGORIES.CONSUMER.value)

        for wallet in consumer_wallet:
            message = f"Sie haben für Ihr Wallet {wallet.wallet_id} noch keine Gutschrift angefordert. Falls Sie eine Gutschrift erhalten möchten, tippen Sie auf 'Gutschrift anfordern' und verifizieren Sie sich."
            self.__notify_wallet(wallet, message)

        company_wallet = wallets_to_notify.filter(
            category=WALLET_CATEGORIES.COMPANY.value)
        for wallet in consumer_wallet:
            message = f"Sie haben Ihr Wallet {wallet.wallet_id} noch nicht verifiziert. Um Ihr Guthaben in Schweizer Franken, einzutauschen müssen Sie sich verifizien. Tippen Sie auf 'Einlösen' um den Prozess zu starten."
            self.__notify_wallet(wallet, message)

    def __notify_wallet(self, wallet, message):
        devices = FCMDevice.objects.filter(user=wallet.owner)
        self.stdout.write(
            f'Notifying {len(devices)} potential devices with {message}')
        devices.send_message(
            title=settings.PUSH_NOTIFICATION_TITLE, body=message)

    def __notify_wallets(self, wallets, message):
        user_uuids_to_notify = list(set(wallets.values_list('owner')))
        devices = FCMDevice.objects.filter(user__in=user_uuids_to_notify)
        self.stdout.write(
            f'Notifying {len(devices)} potential devices with {message}')
        devices.send_message(
            title=settings.PUSH_NOTIFICATION_TITLE, body=message)
