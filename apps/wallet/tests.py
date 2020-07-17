from django.test import TestCase
from apps.wallet.models import Wallet, TokenTransaction


class WalletTestCase(TestCase):
    def setUp(self):
        pass

    def test_address_calculation(self):
        wallet = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")
        self.assertEqual(
            wallet.nonce, 0)

    def test_nonce_calculation(self):
        wallet1 = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")
        wallet2 = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT")
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=10)
        self.assertEqual(
            wallet1.nonce, 1)
        self.assertEqual(
            wallet2.nonce, 0)
        TokenTransaction.objects.create(
            from_addr=wallet2, to_addr=wallet1, amount=1)
        self.assertEqual(
            wallet1.nonce, 1)
        self.assertEqual(
            wallet2.nonce, 1)
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=1)
        self.assertEqual(
            wallet1.nonce, 2)
        self.assertEqual(
            wallet2.nonce, 1)

    def test_balance_calculation(self):
        wallet1 = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")
        wallet2 = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT")
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=10)
        self.assertEqual(
            wallet1.balance, -10)
        self.assertEqual(
            wallet2.balance, 10)
        TokenTransaction.objects.create(
            from_addr=wallet2, to_addr=wallet1, amount=1)
        self.assertEqual(
            wallet1.balance, -9)
        self.assertEqual(
            wallet2.balance, 9)
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=1)
        self.assertEqual(
            wallet1.balance, -10)
        self.assertEqual(
            wallet2.balance, 10)
