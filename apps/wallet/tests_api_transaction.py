import pytezos
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.currency.models import Currency
from apps.wallet.models import (WALLET_STATES, MetaTransaction, Transaction,
                                Wallet)
from apps.wallet.serializers import TransactionSerializer, WalletSerializer
from apps.wallet.utils import (pack_meta_transaction,
                               read_nonce_from_chain)
from django.core.exceptions import ValidationError


class TransactionApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")

        self.currency = Currency.objects.create(token_id=0, name="TEZ", symbol='tez', claim_deadline='2120-01-01', campaign_end='2120-01-01')
        self.currency_2 = Currency.objects.create(token_id=1, name="TEZ2", symbol='tez2', claim_deadline='2120-01-01', campaign_end='2120-01-01')

        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku8CQWKpekx9EWYKPF3pPScPeo3acTEKdeA9vdJYU8hSgoFPq53", currency=self.currency)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkusN6THUuQ5cJV1wWGURe23Mp4G9qFVgh8Pfh8BcMLT9CziPDVx", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_2, currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_2_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_1, currency=self.currency_2, state=WALLET_STATES.VERIFIED.value)

        self.key = pytezos.Key.from_encoded_key(
            settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY)

        self.wallet_pk = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.key.public_key(), currency=self.currency, owner=self.user)

    def test_transaction_create_unauthorized(self):
        # add money to wallet
        Transaction.objects.create(to_wallet=self.wallet_pk, amount=20)

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': 1
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transaction_create_not_verified(self):
        self.client.force_authenticate(user=self.user)

        # add money to wallet
        tx1_1 = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=150)

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        tx_count = MetaTransaction.objects.all().count()

        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(tx_count, MetaTransaction.objects.all().count())

    def test_transaction_create_different_currency(self):
        self.client.force_authenticate(user=self.user)
        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()

        # add money to wallet
        tx1_1 = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=150)

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2_2, nonce=self.wallet_pk.nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        tx_count = MetaTransaction.objects.all().count()

        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(tx_count, MetaTransaction.objects.all().count())

    def test_transaction_create_nonce_issue(self):
        self.client.force_authenticate(user=self.user)
        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()

        # add money to wallet
        tx1_1 = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=150)

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        tx_count = MetaTransaction.objects.all().count()
        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+2
        })
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(tx_count, MetaTransaction.objects.all().count())

    def test_transaction_create_balance_too_small(self):
        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()
        self.client.force_authenticate(user=self.user)

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=20)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        tx_count = MetaTransaction.objects.all().count()
        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 200,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(tx_count, MetaTransaction.objects.all().count())

    def test_transaction_create_signature_invalid(self):
        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()
        self.client.force_authenticate(user=self.user)

        # add money to wallet
        tx1_1 = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=150)

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=20)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = self.key.sign(packed_meta_transaction)

        tx_count = MetaTransaction.objects.all().count()

        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(tx_count, MetaTransaction.objects.all().count())

    def test_transaction_create_correct(self):
        self.client.force_authenticate(user=self.user)
        self.wallet_pk.state = WALLET_STATES.VERIFIED.value
        self.wallet_pk.save()

        # add money to wallet
        tx1_1 = Transaction.objects.create(
            to_wallet=self.wallet_pk, amount=150)

        tx_count = MetaTransaction.objects.all().count()

        # create signature
        token_transaction = MetaTransaction(
            from_wallet=self.wallet_pk, to_wallet=self.wallet_2, nonce=self.wallet_pk.nonce+1, amount=10)
        signature = self.key.sign(pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary()))

        response = self.client.post('/api/wallet/meta_transaction/', {
            'from_wallet': self.wallet_pk.wallet_id,
            'to_wallet': self.wallet_2.wallet_id,
            'amount': 10,
            'signature': signature,
            'nonce': self.wallet_pk.nonce+1
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tx_count+1, MetaTransaction.objects.all().count())

        self.client.force_authenticate(user=None)

    def test_transaction_list(self):
        tx1_1 = Transaction.objects.create(
            to_wallet=self.wallet_1, amount=20)
        tx2_1 = Transaction.objects.create(
            to_wallet=self.wallet_2_2, amount=20)
        tx3_1 = Transaction.objects.create(
            to_wallet=self.wallet_2, amount=20)

        response = self.client.get('/api/wallet/transaction/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user_3 = get_user_model().objects.create(
            username="testuser_3", password="abcd")

        self.client.force_authenticate(user=user_3)

        response = self.client.get('/api/wallet/transaction/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/wallet/transaction/')
        response_result = [dict(r) for r in response.data['results']]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data, [TransactionSerializer(
        #   tx1).data, TransactionSerializer(tx2).data, TransactionSerializer(tx1_1).data])

        self.client.force_authenticate(user=None)
