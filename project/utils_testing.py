import pytezos
from django.contrib.auth import get_user_model
from django.test.client import Client
from rest_framework.test import APITestCase

from apps.currency.models import Currency
from apps.verification.models import PlaceOfOrigin, UserVerification
from apps.wallet.models import (
    WALLET_CATEGORIES,
    WALLET_STATES,
    MetaTransaction,
    PaperWallet,
    Transaction,
    Wallet,
)
from apps.wallet.utils import pack_meta_transaction


class EcouponTestCaseMixin:
    pubkey_1 = "edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG"
    pubkey_2 = "edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg"

    def setUp(self):
        super().setUp()
        self.staff_user = get_user_model().objects.create(
            username="staff1", password="staff1", is_staff=True
        )

        self.user = get_user_model().objects.create(
            username="testuser", password="abcd"
        )
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd"
        )
        self.currency = Currency.objects.create(
            token_id=0,
            name="TEZ",
            symbol="tez",
            claim_deadline="2120-01-01",
            campaign_end="2120-01-01",
        )

        self.currency_2 = Currency.objects.create(
            token_id=0,
            name="TEZ_2",
            symbol="tez_2",
            claim_deadline="2120-01-01",
            campaign_end="2120-01-01",
            is_public=True,
        )
        self.wallet_1 = Wallet.objects.create(
            owner=self.user,
            wallet_id=Wallet.generate_wallet_id(),
            public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R",
            currency=self.currency,
            state=WALLET_STATES.VERIFIED.value,
        )
        self.wallet_1_2 = Wallet.objects.create(
            owner=self.user,
            wallet_id=Wallet.generate_wallet_id(),
            public_key="edpkvToUKgksWQimEUNSpf7trGnTGkcmq1EtEh77QUhCVxHiHBjwcN",
            currency=self.currency,
            state=WALLET_STATES.VERIFIED.value,
        )

        self.wallet_1_2_2 = Wallet.objects.create(
            owner=self.user,
            wallet_id=Wallet.generate_wallet_id(),
            public_key="edpkv6gj831MrqPr7WSBVLk7FSy2j1yrvy4yZ97enpWeQDASB28n6D",
            currency=self.currency_2,
            state=WALLET_STATES.VERIFIED.value,
        )

        self.wallet_2 = Wallet.objects.create(
            owner=self.user_2,
            wallet_id=Wallet.generate_wallet_id(),
            public_key="edpkutu49fgbHxV6vdVRBLbvCLpuq7CmSR6pnowxZRFcY7c76wUqHT",
            currency=self.currency,
            state=WALLET_STATES.VERIFIED.value,
        )

        self.wallet_2_2 = Wallet.objects.create(
            owner=self.user_2,
            wallet_id=Wallet.generate_wallet_id(),
            public_key="edpkvH2qAmRHSZLHidBcuqtbeyxhGwQQkfxhEYrRYXgpahgunjQnFM",
            currency=self.currency_2,
            state=WALLET_STATES.VERIFIED.value,
        )

        key = pytezos.crypto.key.Key.generate()
        private_key = key.secret_key(None, False)
        public_key = key.public_key()

        self.paper_wallet_1 = PaperWallet.objects.create(
            currency=self.currency,
            private_key=private_key,
            wallet_id=PaperWallet.generate_wallet_id(),
            public_key=public_key,
            category=WALLET_CATEGORIES.CONSUMER.value,
        )

        key = pytezos.crypto.key.Key.generate()
        private_key = key.secret_key(None, False)
        public_key = key.public_key()

        self.paper_wallet_2 = PaperWallet.objects.create(
            currency=self.currency_2,
            private_key=private_key,
            wallet_id=PaperWallet.generate_wallet_id(),
            public_key=public_key,
            category=WALLET_CATEGORIES.CONSUMER.value,
        )

        user_verification = UserVerification.objects.create(
            first_name="Alessandro11",
            last_name="De Carli11",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )
        place_of_origin = PlaceOfOrigin.objects.create(
            place_of_origin="Baden AG", user_verification=user_verification
        )
        self.paper_wallet = PaperWallet.generate_new_wallet(
            self.currency, place_of_origin, user_verification
        )

        self.currency.cashout_wallet = self.wallet_2
        self.currency.save()

        # TRANSACTIONS
        Transaction.objects.create(to_wallet=self.currency.owner_wallet, amount=2000)
        Transaction.objects.create(to_wallet=self.currency_2.owner_wallet, amount=2000)

        Transaction.objects.create(to_wallet=self.wallet_1, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_1_2, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_1_2_2, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_2, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_2_2, amount=20)

        key = pytezos.crypto.key.Key.generate()
        self.wallet_1.public_key = key.public_key()
        self.wallet_1.save()
        meta_token_transaction = MetaTransaction(
            from_wallet=self.wallet_1, to_wallet=self.wallet_2, nonce=1, amount=1
        )
        packed_meta_transaction = pack_meta_transaction(
            meta_token_transaction.to_meta_transaction_dictionary()
        )
        signature = key.sign(packed_meta_transaction)
        MetaTransaction.objects.create(
            from_wallet=self.wallet_1,
            to_wallet=self.wallet_2,
            signature=signature,
            nonce=1,
            amount=1,
        )

        key_2 = pytezos.crypto.key.Key.generate()
        self.wallet_1_2_2.public_key = key_2.public_key()
        self.wallet_1_2_2.save()

        meta_token_transaction = MetaTransaction(
            from_wallet=self.wallet_1_2_2, to_wallet=self.wallet_2_2, nonce=1, amount=1
        )
        packed_meta_transaction = pack_meta_transaction(
            meta_token_transaction.to_meta_transaction_dictionary()
        )
        signature = key_2.sign(packed_meta_transaction)
        MetaTransaction.objects.create(
            from_wallet=self.wallet_1_2_2,
            to_wallet=self.wallet_2_2,
            signature=signature,
            nonce=1,
            amount=1,
        )


class BaseEcouponApiTestCase(EcouponTestCaseMixin, APITestCase):
    pass
