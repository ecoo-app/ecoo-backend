import pytezos
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.currency.models import Currency
from apps.wallet.models import WALLET_STATES, CashOutRequest, Transaction, MetaTransaction, Wallet, WalletPublicKeyTransferRequest
from apps.wallet.serializers import WalletSerializer, WalletPublicKeyTransferRequestSerializer
from apps.wallet.utils import (pack_meta_transaction,
                               publish_open_meta_transactions_to_chain,
                               read_nonce_from_chain)
from django.db.utils import IntegrityError


class WalletApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")
        self.currency = Currency.objects.create(token_id=0, name="TEZ")
        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22r", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.currency = Currency.objects.create(token_id=0, name="TEZ")

    # TODO: create test to check the wallet category

    def test_create_wallet_unauthorized(self):
        wallet_count = Wallet.objects.all().count()
        response = self.client.post('/api/wallet/wallet/', {
            "public_key": self.pubkey_1,
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

    def test_create_wallet_authorized_bad_request(self):
        wallet_count = Wallet.objects.all().count()

        self.client.force_authenticate(user=self.user)

        # bad requests
        response = self.client.post('/api/wallet/wallet/', {
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        response = self.client.post('/api/wallet/wallet/', {
            "public_key": self.pubkey_1,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

    def test_wallet_correct_and_duplicate(self):
        # correct request
        self.client.force_authenticate(user=self.user)

        wallet_count = Wallet.objects.all().count()

        response = self.client.post('/api/wallet/wallet/', {
            "public_key": self.pubkey_1,
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wallet_count+1, Wallet.objects.all().count())

        # duplicate input
        wallet_count = Wallet.objects.all().count()

        response = self.client.post('/api/wallet/wallet/', {
            "public_key": self.pubkey_1,
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        self.client.force_authenticate(user=None)

    def test_wallet_detail_unauthorized(self):
        response = self.client.get(
            '/api/wallet/wallet/' + self.wallet_1.wallet_id+'/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wallet_detail_authorized(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            '/api/wallet/wallet/' + self.wallet_2.wallet_id+'/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, WalletSerializer(self.wallet_2).data)

        response = self.client.get(
            '/api/wallet/wallet/' + self.wallet_1.wallet_id+'/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, WalletSerializer(self.wallet_1).data)

    def test_list_wallets(self):
        response = self.client.get('/api/wallet/wallet/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/wallet/wallet/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [WalletSerializer(
            self.wallet_1).data, WalletSerializer(self.wallet_1_2).data])

        self.client.force_authenticate(user=None)


class WalletPublicKeyTransferRequestApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")
        self.currency = Currency.objects.create(token_id=0, name="TEZ")
        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f", currency=self.currency)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22r", currency=self.currency)

    def test_create_wallet_public_key_transfer_request_unauthorized(self):
        wallet_public_key_transfer_request_count = WalletPublicKeyTransferRequest.objects.all().count()
        response = self.client.post('/api/wallet/wallet_public_key_transfer_request/', {
            "wallet": self.wallet_1.uuid,
            "new_public_key": self.pubkey_1
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wallet_public_key_transfer_request_count,
                         WalletPublicKeyTransferRequest.objects.all().count())

    def test_wallet_public_key_transfer_request_correct_and_duplicate(self):
        #   incorrect request
        self.client.force_authenticate(user=self.user_2)

        wallet_public_key_transfer_request_count = WalletPublicKeyTransferRequest.objects.all().count()
        response = self.client.post('/api/wallet/wallet_public_key_transfer_request/', {
            "wallet": self.wallet_1.uuid,
            "new_public_key": self.pubkey_1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wallet_public_key_transfer_request_count,
                         WalletPublicKeyTransferRequest.objects.all().count())

    def test_wallet_public_key_transfer_request_correct_and_duplicate(self):
        # correct request
        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = WalletPublicKeyTransferRequest.objects.all().count()
        response = self.client.post('/api/wallet/wallet_public_key_transfer_request/', {
            "wallet": self.wallet_1.uuid,
            "new_public_key": self.pubkey_1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wallet_public_key_transfer_request_count +
                         1, WalletPublicKeyTransferRequest.objects.all().count())

    def test_wallet_public_key_transfer_request_list(self):
        # correct request
        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = WalletPublicKeyTransferRequest.objects.all().count()
        response = self.client.post('/api/wallet/wallet_public_key_transfer_request/', {
            "wallet": self.wallet_1.uuid,
            "new_public_key": self.pubkey_1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wallet_public_key_transfer_request_count +
                         1, WalletPublicKeyTransferRequest.objects.all().count())

        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = WalletPublicKeyTransferRequest.objects.all().count()
        response = self.client.get(
            '/api/wallet/wallet_public_key_transfer_request/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], list(map(lambda wallet_public_key_transfer_request: WalletPublicKeyTransferRequestSerializer(
            wallet_public_key_transfer_request).data, WalletPublicKeyTransferRequest.objects.all())))

        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            '/api/wallet/wallet_public_key_transfer_request/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])


class CashOutRequestApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")
        self.currency = Currency.objects.create(token_id=0, name="TEZ")
        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22r", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.key = pytezos.Key.from_encoded_key(
            settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY)
        self.wallet_pk = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.key.public_key(), currency=self.currency, owner=self.user, state=WALLET_STATES.VERIFIED.value)

        self.mint_transaction = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=100)

        self.token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.currency.owner_wallet, nonce=self.wallet_pk.nonce+1, amount=10)
        signature = self.key.sign(pack_meta_transaction(
            self.token_transaction.to_meta_transaction_dictionary()))
        self.token_transaction.signature = signature
        self.token_transaction.save()

    def test_create_cash_out_request_unauthorized(self):
        cash_out_request_count = CashOutRequest.objects.all().count()
        response = self.client.post('/api/wallet/cash_out_request/', {
            "transaction": self.token_transaction.uuid,
            "beneficiary_name": "Papers AG",
            "beneficiary_iban": "CH2509000000619652574"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(cash_out_request_count,
                         CashOutRequest.objects.all().count())

    def test_create_cash_out_request_bad_user(self):
        cash_out_request_count = CashOutRequest.objects.all().count()
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post('/api/wallet/cash_out_request/', {
            "transaction": self.token_transaction.uuid,
            "beneficiary_name": "Papers AG",
            "beneficiary_iban": "CH2509000000619652574"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cash_out_request_count,
                         CashOutRequest.objects.all().count())

    def test_create_cash_out_request_correct_and_duplicate(self):
        # correct request
        cash_out_request_count = CashOutRequest.objects.all().count()
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/wallet/cash_out_request/', {
            "transaction": self.token_transaction.uuid,
            "beneficiary_name": "Papers AG",
            "beneficiary_iban": "CH2509000000619652574"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(cash_out_request_count +
                         1, CashOutRequest.objects.all().count())

        cash_out_request_count = CashOutRequest.objects.all().count()
        self.client.force_authenticate(user=self.user)
        wallet_public_key_transfer_request_count = WalletPublicKeyTransferRequest.objects.all().count()
        with self.assertRaises(IntegrityError):
            response = self.client.post('/api/wallet/cash_out_request/', {
                "transaction": self.token_transaction.uuid,
                "beneficiary_name": "Papers AG",
                "beneficiary_iban": "CH2509000000619652574"
            }, format='json')
