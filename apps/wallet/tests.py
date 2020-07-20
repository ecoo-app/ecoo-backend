from django.test import TestCase
from apps.wallet.models import Wallet, TokenTransaction, TRANSACTION_STATES
from pytezos import pytezos, michelson
from apps.wallet.utils import publish_open_meta_transactions_to_chain, pack_meta_transaction, read_nonce_from_chain
import time
from django.conf import settings


class WalletTestCase(TestCase):
    def setUp(self):
        pass

    def test_address_calculation(self):
        wallet = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")
        self.assertEqual(
            wallet.nonce, 0)

    def test_nonce_calculation(self):
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT")
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=10, nonce=1)
        self.assertEqual(
            wallet1.nonce, 1)
        self.assertEqual(
            wallet2.nonce, 0)
        TokenTransaction.objects.create(
            from_addr=wallet2, to_addr=wallet1, amount=1, nonce=2)
        self.assertEqual(
            wallet1.nonce, 1)
        self.assertEqual(
            wallet2.nonce, 1)
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=1, nonce=3)
        self.assertEqual(
            wallet1.nonce, 2)
        self.assertEqual(
            wallet2.nonce, 1)

    def test_balance_calculation(self):
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R")
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT")
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=10, nonce=1)
        self.assertEqual(
            wallet1.balance, -10)
        self.assertEqual(
            wallet2.balance, 10)
        TokenTransaction.objects.create(
            from_addr=wallet2, to_addr=wallet1, amount=1, nonce=2)
        self.assertEqual(
            wallet1.balance, -9)
        self.assertEqual(
            wallet2.balance, 9)
        TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, amount=1, nonce=3)
        self.assertEqual(
            wallet1.balance, -10)
        self.assertEqual(
            wallet2.balance, 10)


class BlockchainSyncTestCase(TestCase):
    def setUp(self):
        pass

    def test_transfer(self):
        pytezos_client = pytezos.using(
            key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
        last_nonce = read_nonce_from_chain(
            pytezos_client.key.public_key_hash())
        token_contract = pytezos_client.contract(
            settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
        wallet1 = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key=pytezos_client.key.public_key())
        wallet2 = Wallet.objects.create(walletID=Wallet.getWalletID(
        ), pub_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT")
        token_transaction = TokenTransaction.objects.create(
            from_addr=wallet1, to_addr=wallet2, nonce=last_nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = pytezos_client.key.sign(packed_meta_transaction)
        token_transaction.signature = signature
        token_transaction.save()
        self.assertEqual(token_transaction.state,
                         TRANSACTION_STATES.OPEN.value)
        publish_open_meta_transactions_to_chain()

        token_transaction = TokenTransaction.objects.get(
            pk=token_transaction.pk)

        self.assertEqual(token_transaction.state,
                         TRANSACTION_STATES.DONE.value)
