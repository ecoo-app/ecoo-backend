import pytezos
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.currency.models import Currency
from apps.wallet.models import WALLET_STATES, MetaTransaction, Wallet
from apps.wallet.serializers import PublicWalletSerializer, WalletSerializer
from apps.wallet.utils import (pack_meta_transaction,
                               publish_open_meta_transactions_to_chain,
                               read_nonce_from_chain)


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
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f", currency=self.currency)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22r", currency=self.currency)

        self.currency = Currency.objects.create(token_id=0, name="TEZ")

    # TODO: create test to check the wallet category 

    def test_create_wallet_unauthorized(self):
        wallet_count = Wallet.objects.all().count()
        response = self.client.post('/api/wallet/wallet/create/', {
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

    def test_wallet_correct_and_duplicate(self):
        # correct request
        self.client.force_authenticate(user=self.user)

        wallet_count = Wallet.objects.all().count()

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
