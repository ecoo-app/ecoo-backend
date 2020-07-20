import pytezos
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase
from apps.wallet.utils import publish_open_meta_transactions_to_chain, pack_meta_transaction, read_nonce_from_chain

from apps.currency.models import Currency
from apps.wallet.models import Wallet, TokenTransaction, WALLET_STATES
from apps.wallet.serializers import PublicWalletSerializer, WalletSerializer


class WalletApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")

        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f")

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22r")

        self.currency = Currency.objects.create(token_id=0, name="TEZ")

    def test_create_wallet_unauthorized(self):
        wallet_count = Wallet.objects.all().count()
        response = self.client.post('/api/wallet/wallet/create/', {
            "public_key": self.pubkey_1,
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

    def test_create_wallet_authorized(self):
        wallet_count = Wallet.objects.all().count()

        self.client.force_authenticate(user=self.user)

        # bad requests
        response = self.client.post('/api/wallet/wallet/create/', {
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        response = self.client.post('/api/wallet/wallet/create/', {
            "public_key": self.pubkey_1,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        # correct request
        response = self.client.post('/api/wallet/wallet/create/', {
            "public_key": self.pubkey_1,
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(wallet_count+1, Wallet.objects.all().count())

        # duplicate input
        wallet_count = Wallet.objects.all().count()

        response = self.client.post('/api/wallet/wallet/create/', {
            "public_key": self.pubkey_1,
            "currency": self.currency.uuid,
            "is_company_wallet": False
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wallet_count, Wallet.objects.all().count())

        self.client.force_authenticate(user=None)

    def test_wallet_detail(self):
        # unauthorized
        response = self.client.get(
            '/api/wallet/wallet/' + self.wallet_1.wallet_id+'/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # authorized
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            '/api/wallet/wallet/' + self.wallet_2.wallet_id+'/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, PublicWalletSerializer(self.wallet_2).data)

        response = self.client.get(
            '/api/wallet/wallet/' + self.wallet_1.wallet_id+'/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, WalletSerializer(self.wallet_1).data)

    def test_list_wallets(self):
        response = self.client.get('/api/wallet/wallet/list/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/wallet/wallet/list/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [WalletSerializer(
            self.wallet_1).data, WalletSerializer(self.wallet_1_2).data])

        self.client.force_authenticate(user=None)


class TransactionApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")

        self.currency = Currency.objects.create(token_id=0, name="TEZ")
        self.currency_2 = Currency.objects.create(token_id=1, name="TEZ2")

        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f")

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_2, currency=self.currency)


    def test_transaction_create_unauthorized(self):

        key = pytezos.Key.from_encoded_key(
            settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY)

        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=key.public_key(), currency=self.currency, owner=self.user)

        last_nonce = read_nonce_from_chain(key.public_key_hash())
        token_transaction = TokenTransaction.objects.create(
            from_wallet=wallet1, to_wallet=self.wallet_2, nonce=last_nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = key.sign(packed_meta_transaction)

        token_transaction.delete()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': wallet1.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': last_nonce+1
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transaction_create(self):

        key = pytezos.Key.from_encoded_key(
            settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY)

        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=key.public_key(), currency=self.currency, owner=self.user)

        last_nonce = read_nonce_from_chain(key.public_key_hash())

        token_transaction = TokenTransaction.objects.create(
            from_wallet=wallet1, to_wallet=self.wallet_2, nonce=last_nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = key.sign(packed_meta_transaction)
        token_transaction.delete()

        self.client.force_authenticate(user=self.user)

        tx_count = TokenTransaction.objects.all().count()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': wallet1.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': last_nonce+1
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(tx_count, TokenTransaction.objects.all().count())

        wallet1.state = WALLET_STATES.VERIFIED.value
        wallet1.save()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': wallet1.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': last_nonce+1
        })
        print(response)
        print(response.data)
        

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tx_count+1, TokenTransaction.objects.all().count())

        self.client.force_authenticate(user=None)

    def test_transaction_list(self):
        pass
