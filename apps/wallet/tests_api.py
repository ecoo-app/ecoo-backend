import pytezos
from django.conf import settings
from rest_framework import status

from apps.wallet.models import (
    WALLET_CATEGORIES,
    WALLET_STATES,
    CashOutRequest,
    MetaTransaction,
    Transaction,
    Wallet,
    WalletPublicKeyTransferRequest,
)
from apps.wallet.serializers import (
    CashOutRequestSerializer,
    PublicWalletSerializer,
    WalletPublicKeyTransferRequestSerializer,
    WalletSerializer,
)
from apps.wallet.utils import create_paper_wallet_message, pack_meta_transaction
from project.utils_testing import BaseEcouponApiTestCase


class WalletApiTest(BaseEcouponApiTestCase):
    def setUp(self):
        super().setUp()

    # TODO: create test to check the wallet category

    def test_create_wallet_unauthorized(self):
        wallet_count = Wallet.objects.all().count()
        response = self.client.post(
            "/api/wallet/wallet/",
            {"public_key": self.pubkey_1, "currency": self.currency.uuid},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

    def test_create_wallet_owner_category(self):
        # correct request
        self.client.force_authenticate(user=self.user)

        wallet_count = Wallet.objects.all().count()

        response = self.client.post(
            "/api/wallet/wallet/",
            {
                "public_key": self.pubkey_1,
                "currency": self.currency.uuid,
                "category": WALLET_CATEGORIES.OWNER.value,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

    def test_create_wallet_authorized_bad_request(self):
        wallet_count = Wallet.objects.all().count()

        self.client.force_authenticate(user=self.user)

        # bad requests
        response = self.client.post(
            "/api/wallet/wallet/", {"currency": self.currency.uuid}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        response = self.client.post(
            "/api/wallet/wallet/", {"public_key": self.pubkey_1}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

    def test_wallet_correct_and_duplicate(self):
        # correct request
        self.client.force_authenticate(user=self.user)

        wallet_count = Wallet.objects.all().count()

        response = self.client.post(
            "/api/wallet/wallet/",
            {"public_key": self.pubkey_1, "currency": self.currency.uuid},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wallet_count + 1, Wallet.objects.all().count())

        # duplicate input
        wallet_count = Wallet.objects.all().count()

        response = self.client.post(
            "/api/wallet/wallet/",
            {"public_key": self.pubkey_1, "currency": self.currency.uuid},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        self.client.force_authenticate(user=None)

    def test_wallet_detail_unauthorized(self):
        response = self.client.get(
            "/api/wallet/wallet/" + self.wallet_1.wallet_id + "/"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wallet_detail_authorized(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/api/wallet/wallet/" + self.wallet_2.wallet_id + "/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, PublicWalletSerializer(self.wallet_2).data)

        response = self.client.get(
            "/api/wallet/wallet/" + self.wallet_1.wallet_id + "/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, WalletSerializer(self.wallet_1).data)

    def test_paper_wallet_detail_unauthorized(self):
        response = self.client.get(
            "/api/wallet/paper_wallet/" + self.paper_wallet.wallet_id + "/"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_paper_wallet_detail_authorized(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/api/wallet/paper_wallet/" + self.paper_wallet.wallet_id + "/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, PublicWalletSerializer(self.paper_wallet).data)

        # invalid signature gives bad request
        signature = "abcd"
        response = self.client.get(
            "/api/wallet/paper_wallet/"
            + self.paper_wallet.wallet_id
            + "/"
            + signature
            + "/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        key = pytezos.Key.from_encoded_key(self.paper_wallet.private_key)
        signature = key.sign(
            create_paper_wallet_message(
                self.paper_wallet, self.paper_wallet.currency.token_id
            )
        )

        response = self.client.get(
            "/api/wallet/paper_wallet/"
            + self.paper_wallet.wallet_id
            + "/"
            + signature
            + "/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, WalletSerializer(self.paper_wallet).data)

    def test_list_wallets(self):
        response = self.client.get("/api/wallet/wallet/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/wallet/wallet/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"],
            [
                WalletSerializer(self.wallet_1_2_2).data,
                WalletSerializer(self.wallet_1_2).data,
                WalletSerializer(self.wallet_1).data,
            ],
        )

        self.client.force_authenticate(user=None)

    def test_list_wallets_is_public_filter(self):
        response = self.client.get("/api/wallet/wallet/?currency__is_public=true")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/wallet/wallet/?currency__is_public=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"],
            [
                WalletSerializer(self.wallet_1_2_2).data,
            ],
        )

        self.client.force_authenticate(user=None)

        response = self.client.get("/api/wallet/wallet/?currency__is_public=false")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/wallet/wallet/?currency__is_public=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"],
            [
                WalletSerializer(self.wallet_1_2).data,
                WalletSerializer(self.wallet_1).data,
            ],
        )

        self.client.force_authenticate(user=None)


class WalletPublicKeyTransferRequestApiTest(BaseEcouponApiTestCase):
    def setUp(self):
        super().setUp()

    def test_create_wallet_public_key_transfer_request_unauthorized(self):
        wallet_public_key_transfer_request_count = (
            WalletPublicKeyTransferRequest.objects.all().count()
        )
        response = self.client.post(
            "/api/wallet/wallet_public_key_transfer_request/",
            {"wallet": self.wallet_1.uuid, "new_public_key": self.pubkey_1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            wallet_public_key_transfer_request_count,
            WalletPublicKeyTransferRequest.objects.all().count(),
        )

    # FIXME: was overriden by test with same name!
    def test_wallet_public_key_transfer_request_correct_and_duplicate(self):
        #   incorrect request
        self.client.force_authenticate(user=self.user_2)

        wallet_public_key_transfer_request_count = (
            WalletPublicKeyTransferRequest.objects.all().count()
        )
        response = self.client.post(
            "/api/wallet/wallet_public_key_transfer_request/",
            {"wallet": self.wallet_1.wallet_id, "new_public_key": self.pubkey_1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            wallet_public_key_transfer_request_count,
            WalletPublicKeyTransferRequest.objects.all().count(),
        )

    def test_wallet_public_key_transfer_request_correct_and_duplicate_1(self):
        # correct request
        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = (
            WalletPublicKeyTransferRequest.objects.all().count()
        )
        response = self.client.post(
            "/api/wallet/wallet_public_key_transfer_request/",
            {"wallet": self.wallet_1.wallet_id, "new_public_key": self.pubkey_1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            wallet_public_key_transfer_request_count + 1,
            WalletPublicKeyTransferRequest.objects.all().count(),
        )

    def test_wallet_public_key_transfer_request_list(self):
        # correct request
        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = (
            WalletPublicKeyTransferRequest.objects.all().count()
        )
        response = self.client.post(
            "/api/wallet/wallet_public_key_transfer_request/",
            {"wallet": self.wallet_1.wallet_id, "new_public_key": self.pubkey_1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            wallet_public_key_transfer_request_count + 1,
            WalletPublicKeyTransferRequest.objects.all().count(),
        )

        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = (
            WalletPublicKeyTransferRequest.objects.all().count()
        )
        response = self.client.get("/api/wallet/wallet_public_key_transfer_request/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"],
            list(
                map(
                    lambda wallet_public_key_transfer_request: WalletPublicKeyTransferRequestSerializer(
                        wallet_public_key_transfer_request
                    ).data,
                    WalletPublicKeyTransferRequest.objects.all(),
                )
            ),
        )

        self.client.force_authenticate(user=self.user_2)
        response = self.client.get("/api/wallet/wallet_public_key_transfer_request/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])


class CashOutRequestApiTest(BaseEcouponApiTestCase):
    def setUp(self):
        super().setUp()

        self.key = pytezos.Key.from_encoded_key(
            settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY
        )
        self.wallet_pk = Wallet.objects.create(
            wallet_id=Wallet.generate_wallet_id(),
            public_key=self.key.public_key(),
            currency=self.currency,
            owner=self.user,
            state=WALLET_STATES.VERIFIED.value,
        )

        self.mint_transaction = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=100
        )

        self.token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk,
            to_wallet=self.currency.cashout_wallet,
            nonce=self.wallet_pk.nonce + 1,
            amount=10,
        )
        signature = self.key.sign(
            pack_meta_transaction(
                self.token_transaction.to_meta_transaction_dictionary()
            )
        )
        self.token_transaction.signature = signature
        self.token_transaction.save()

    def test_create_cash_out_request_unauthorized(self):
        cash_out_request_count = CashOutRequest.objects.all().count()
        response = self.client.post(
            "/api/wallet/cash_out_request/",
            {
                "transaction": self.token_transaction.uuid,
                "beneficiary_name": "Papers AG",
                "beneficiary_iban": "CH2509000000619652574",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(cash_out_request_count, CashOutRequest.objects.all().count())

    def test_create_cash_out_request_bad_user(self):
        cash_out_request_count = CashOutRequest.objects.all().count()
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            "/api/wallet/cash_out_request/",
            {
                "transaction": self.token_transaction.uuid,
                "beneficiary_name": "Papers AG",
                "beneficiary_iban": "CH2509000000619652574",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cash_out_request_count, CashOutRequest.objects.all().count())

    def test_create_cash_out_request_correct_and_duplicate(self):
        # correct request
        cash_out_request_count = CashOutRequest.objects.all().count()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/wallet/cash_out_request/",
            {
                "transaction": self.token_transaction.uuid,
                "beneficiary_name": "Papers AG",
                "beneficiary_iban": "CH2509000000619652574",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            cash_out_request_count + 1, CashOutRequest.objects.all().count()
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/wallet/cash_out_request/",
            {
                "transaction": self.token_transaction.uuid,
                "beneficiary_name": "Papers AG",
                "beneficiary_iban": "CH2509000000619652574",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_cash_out_request_list(self):
        # correct request
        self.client.force_authenticate(user=self.user)
        CashOutRequest.objects.all().delete()
        response = self.client.post(
            "/api/wallet/cash_out_request/",
            {
                "transaction": self.token_transaction.uuid,
                "beneficiary_name": "Papers AG",
                "beneficiary_iban": "CH2509000000619652574",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/wallet/cash_out_request/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"],
            list(
                map(
                    lambda cash_out_request: CashOutRequestSerializer(
                        cash_out_request
                    ).data,
                    CashOutRequest.objects.all(),
                )
            ),
        )

        self.client.force_authenticate(user=self.user_2)
        response = self.client.get("/api/wallet/cash_out_request/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])
