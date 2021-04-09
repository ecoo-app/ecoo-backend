from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from apps.currency.models import Currency
from apps.wallet.models import WALLET_CATEGORIES
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
            "--n",
            default=10,
            help="number of wallets to create",
        )

        parser.add_argument(
            "--currency",
            default="test_currency",
            help="name of the currency to use",
        )

        parser.add_argument(
            "--create_zip",
            default="False",
            help="should a zip file be created containing all the qr's",
        )

        parser.add_argument(
            "--debug",
            default="False",
            help="print detailed debug logs",
        )

    def handle(self, *args, **options):
        if not Currency.objects.filter(name=options["currency"]).exists():
            self.stdout.write(f"Currency '{options['currency']}' does not exist")
            return
        currency = Currency.objects.get(name=options["currency"])
        n = int(options["n"])

        if options["debug"] not in ["True", "False", "false", "true"]:
            self.stdout.write(
                f"Debug should be one of True true, False, false but was '{options['debug']}'"
            )
            return

        if options["create_zip"] not in ["True", "False", "false", "true"]:
            self.stdout.write(
                f"create_zip should be one of True true, False, false but was '{options['create_zip']}'"
            )
            return

        debug = options["debug"] in ["True", "true"]
        create_zip = options["create_zip"] in ["True", "true"]

        type = None
        if options["type"] == "consumer":
            type = WALLET_CATEGORIES.CONSUMER.value
        if options["type"] == "company":
            type = WALLET_CATEGORIES.COMPANY.value

        if type is None:
            self.stdout.write(f"Invalid type configured: '{options['type']}'")
            return

        if (
            type == WALLET_CATEGORIES.CONSUMER.value
            and n * currency.starting_capital > currency.owner_wallet.balance
        ):
            self.stdout.write(
                f"Currency: {currency.name} has not enough balance on the owner wallet"
            )
            return

        wallet_ids = []
        paper_wallets = []

        self.stdout.write(f"Creating {n} Wallets for currency {currency.name}")

        for i in range(n):
            try:
                paper_wallet = generate_paper_wallet(currency, type)

                if type == WALLET_CATEGORIES.CONSUMER.value:
                    create_claim_transaction(paper_wallet)
                wallet_ids.append(paper_wallet.wallet_id)
                paper_wallets.append(paper_wallet)

                if debug is True:
                    self.stdout.write(paper_wallet.wallet_id)

            except ValidationError as e:
                self.stdout.write(f"Error: {str(e.message)}")

        if debug is True:
            self.stdout.write("Added the following wallet_ids:")
            self.stdout.write(", ".join(wallet_ids))

        if create_zip:
            if debug:
                self.stdout.write("Create zip file")
            zip_file = generate_qr_code_zip(paper_wallets, add_wallet_id_csv=True)
            self.stdout.write(f"Created zip file: {zip_file}")
