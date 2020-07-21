from django.test import TestCase
from apps.currency.models import Currency
from apps.wallet.models import Wallet, MetaTransaction, Transaction, TRANSACTION_STATES
from pytezos import pytezos, michelson
from apps.wallet.utils import publish_open_meta_transactions_to_chain, pack_meta_transaction, read_nonce_from_chain
import time
from django.conf import settings
from django.core.exceptions import ValidationError


class WalletTestCase(TestCase):
    def setUp(self):
        pass

    def test_address_calculation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency)
        self.assertEqual(
            wallet.nonce, 0)

    def test_nonce_calculation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency)
        Transaction.objects.create(to_wallet=wallet1, amount=100)
        MetaTransaction.objects.create(
            from_wallet=wallet1, to_wallet=wallet2, amount=10, nonce=1)
        self.assertEqual(
            wallet1.nonce, 1)
        self.assertEqual(
            wallet2.nonce, 0)
        MetaTransaction.objects.create(
            from_wallet=wallet2, to_wallet=wallet1, amount=1, nonce=2)
        self.assertEqual(
            wallet1.nonce, 1)
        self.assertEqual(
            wallet2.nonce, 1)
        MetaTransaction.objects.create(
            from_wallet=wallet1, to_wallet=wallet2, amount=1, nonce=3)
        self.assertEqual(
            wallet1.nonce, 2)
        self.assertEqual(
            wallet2.nonce, 1)

    def test_balance_calculation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency)
        Transaction.objects.create(to_wallet=wallet1, amount=100)
        MetaTransaction.objects.create(
            from_wallet=wallet1, to_wallet=wallet2, amount=10, nonce=1)
        self.assertEqual(
            wallet1.balance, 90)
        self.assertEqual(
            wallet2.balance, 10)
        MetaTransaction.objects.create(
            from_wallet=wallet2, to_wallet=wallet1, amount=1, nonce=2)
        self.assertEqual(
            wallet1.balance, 91)
        self.assertEqual(
            wallet2.balance, 9)
        MetaTransaction.objects.create(
            from_wallet=wallet1, to_wallet=wallet2, amount=1, nonce=3)
        self.assertEqual(
            wallet1.balance, 90)
        self.assertEqual(
            wallet2.balance, 10)


class MetaTransactionTestCase(TestCase):
    def test_validation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency)

        Transaction.objects.create(to_wallet=wallet1, amount=100)
        with self.assertRaises(ValidationError):
            MetaTransaction.objects.create(
                from_wallet=None, to_wallet=wallet2, amount=10, nonce=1)
        with self.assertRaises(ValidationError):
            MetaTransaction.objects.create(
                from_wallet=wallet1, to_wallet=wallet2, amount=10, nonce=0)
        with self.assertRaises(ValidationError):
            MetaTransaction.objects.create(
                from_wallet=wallet1, to_wallet=wallet2, amount=0, nonce=1)


class TransactionTestCase(TestCase):
    def test_validation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency)

        Transaction.objects.create(to_wallet=wallet1, amount=100)
        currency.allow_minting = False
        currency.save()
        with self.assertRaises(ValidationError):
            Transaction.objects.create(to_wallet=wallet1, amount=100)


class BlockchainSyncTestCase(TestCase):
    def setUp(self):
        pass

    def test_transfer(self):
        currency = Currency.objects.create(token_id=0, name="TEZ")
        pytezos_client = pytezos.using(
            key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
        last_nonce = read_nonce_from_chain(
            pytezos_client.key.public_key_hash())

        token_contract = pytezos_client.contract(
            settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=pytezos_client.key.public_key(), currency=currency)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency)
        Transaction.objects.create(to_wallet=wallet1, amount=100)
        token_transaction = MetaTransaction(
            from_wallet=wallet1, to_wallet=wallet2, nonce=last_nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = pytezos_client.key.sign(packed_meta_transaction)
        token_transaction.signature = signature
        token_transaction.save()
        self.assertEqual(token_transaction.state,
                         TRANSACTION_STATES.OPEN.value)
        publish_open_meta_transactions_to_chain()

        token_transaction = MetaTransaction.objects.get(
            pk=token_transaction.pk)

        self.assertEqual(token_transaction.state,
                         TRANSACTION_STATES.DONE.value)

    def test_transfer(self):
        currency = Currency.objects.create(token_id=0, name="TEZ")
        pytezos_client = pytezos.using(
            key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
        last_nonce = read_nonce_from_chain(
            pytezos_client.key.public_key_hash())

        token_contract = pytezos_client.contract(
            settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=pytezos_client.key.public_key(), currency=currency)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency)
        Transaction.objects.create(to_wallet=wallet1, amount=100)
        token_transaction = MetaTransaction(
            from_wallet=wallet1, to_wallet=wallet2, nonce=last_nonce+1, amount=10)
        packed_meta_transaction = pack_meta_transaction(
            token_transaction.to_meta_transaction_dictionary())
        signature = pytezos_client.key.sign(packed_meta_transaction)
        token_transaction.signature = signature
        token_transaction.save()
        self.assertEqual(token_transaction.state,
                         TRANSACTION_STATES.OPEN.value)
        publish_open_meta_transactions_to_chain()

        token_transaction = MetaTransaction.objects.get(
            pk=token_transaction.pk)

        self.assertEqual(token_transaction.state,
                         TRANSACTION_STATES.DONE.value)
