from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from apps.currency.models import Currency
from apps.wallet.models import WALLET_CATEGORIES, PaperWallet
from apps.wallet.public_utils import generate_paper_wallet, generate_qr_code_zip
from apps.wallet.utils import create_claim_transaction


class Command(BaseCommand):
    help = "Creates multiple paper wallets"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            default="consumer",
            help="type either 'consumer' or 'company'",
        )

        parser.add_argument(
            "--offset",
            default=0,
            help="offset to start adding to zip",
        )

        parser.add_argument(
            "--currency",
            default="test_currency",
            help="name of the currency to use",
        )

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        if not Currency.objects.filter(name=options["currency"]).exists():
            self.stdout.write(f"Currency '{options['currency']}' does not exist")
            return
        currency = Currency.objects.get(name=options["currency"])
        offset = int(options["offset"])

        type = None
        if options["type"] == "consumer":
            type = WALLET_CATEGORIES.CONSUMER.value
        if options["type"] == "company":
            type = WALLET_CATEGORIES.COMPANY.value

        if type is None:
            self.stdout.write(f"Invalid type configured: '{options['type']}'")
            return

        zip_file = generate_qr_code_zip(
            PaperWallet.objects.filter(currency=currency, category=type).order_by(
                "created_at"
            )[offset::],
            add_wallet_id_csv=True,
        )
        self.stdout.write(f"Created zip file: {zip_file}")
