import pytezos
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase
from apps.wallet.utils import publish_open_meta_transactions_to_chain, pack_meta_transaction, read_nonce_from_chain

from apps.currency.models import Currency
from apps.wallet.models import Wallet, TokenTransaction, WALLET_STATES
from apps.wallet.serializers import PublicWalletSerializer, WalletSerializer, TransactionSerializer


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

        self.wallet_2_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_1, currency=self.currency_2)

        self.key = pytezos.Key.from_encoded_key(
            settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY)

        self.wallet_pk = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.key.public_key(), currency=self.currency, owner=self.user)

    def test_transaction_create_unauthorized(self):

        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        token_transaction.delete()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': 1
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transaction_create_errors(self):
        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)
        token_transaction.delete()

        self.client.force_authenticate(user=self.user)

        tx_count = TokenTransaction.objects.all().count()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data, {'detail': 'Only verified addresses can send money'})
        self.assertEqual(tx_count, TokenTransaction.objects.all().count())
        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()

        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2_2, nonce=self.wallet_pk.nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)
        token_transaction.delete()

        self.client.force_authenticate(user=self.user)

        tx_count = TokenTransaction.objects.all().count()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.data, {'detail': 'Both wallets have to belong to the same currency'})
        self.assertEqual(tx_count, TokenTransaction.objects.all().count())

        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)
        token_transaction.delete()

        self.client.force_authenticate(user=self.user)

        tx_count = TokenTransaction.objects.all().count()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+2
        })

        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data, {'detail': 'Nonce value is incorrect'})
        self.assertEqual(tx_count, TokenTransaction.objects.all().count())

        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)
        token_transaction.delete()

        self.client.force_authenticate(user=self.user)

        tx_count = TokenTransaction.objects.all().count()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data, {'detail': 'Balance is too small'})
        self.assertEqual(tx_count, TokenTransaction.objects.all().count())

        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=20)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)
        token_transaction.delete()

        self.client.force_authenticate(user=self.user)

        tx1 = TokenTransaction.objects.create(
            from_wallet=self.wallet_2_2, to_wallet=self.wallet_pk, nonce=1, amount=100)
        tx_count = TokenTransaction.objects.all().count()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data, {'detail': 'Signature is invalid'})
        self.assertEqual(tx_count, TokenTransaction.objects.all().count())

    def test_transaction_create_correct(self):
        self.client.force_authenticate(user=self.user)

        tx1 = TokenTransaction.objects.create(
            from_wallet=self.wallet_2_2, to_wallet=self.wallet_pk, nonce=1, amount=100)

        tx_count = TokenTransaction.objects.all().count()

        token_transaction = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=10)

        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()

        signature = self.key.sign(pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary()))

        token_transaction.delete()

        response = self.client.post('/api/wallet/transaction/create/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tx_count+1, TokenTransaction.objects.all().count())

        self.client.force_authenticate(user=None)

    def test_transaction_list(self):
        tx1 = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2_2, nonce=1, amount=10)
        tx2 = TokenTransaction.objects.create(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2_2, nonce=2, amount=10)

        tx3 = TokenTransaction.objects.create(
            from_wallet=self.wallet_2, to_wallet=self.wallet_2_2, nonce=2, amount=10)

        response = self.client.get('/api/wallet/transaction/list/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user_3 = get_user_model().objects.create(
            username="testuser_3", password="abcd")

        self.client.force_authenticate(user=user_3)

        response = self.client.get('/api/wallet/transaction/list/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/wallet/transaction/list/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [TransactionSerializer(
            tx1).data, TransactionSerializer(tx2).data, ])

        self.client.force_authenticate(user=None)