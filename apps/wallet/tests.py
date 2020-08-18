from django.test import TestCase
from apps.currency.models import Currency
from apps.wallet.models import WALLET_STATES, Wallet, MetaTransaction, Transaction, WalletPublicKeyTransferRequest, TRANSACTION_STATES
from apps.wallet.signals import custom_meta_transaction_validation
from pytezos import pytezos, crypto

from apps.wallet.utils import sync_to_blockchain, pack_meta_transaction, read_nonce_from_chain
import time
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from unittest import skip


class WalletTestCase(TestCase):
    def setUp(self):
        pre_save.disconnect(custom_meta_transaction_validation,
                            sender=MetaTransaction, dispatch_uid='custom_meta_transaction_validation')

    def tearDown(self):
        pre_save.connect(custom_meta_transaction_validation,
                         sender=MetaTransaction, dispatch_uid='custom_meta_transaction_validation')

    def test_address_calculation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency, state=WALLET_STATES.VERIFIED.value)
        self.assertEqual(
            wallet.nonce, 0)

    def test_nonce_calculation(self):
        currency = Currency.objects.create(token_id=0, name="test")
        wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency, state=WALLET_STATES.VERIFIED.value)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency, state=WALLET_STATES.VERIFIED.value)
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
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency, state=WALLET_STATES.VERIFIED.value)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency, state=WALLET_STATES.VERIFIED.value)
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
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=currency, state=WALLET_STATES.VERIFIED.value)
        wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=currency, state=WALLET_STATES.VERIFIED.value)

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

    def setUp(self):
        self.currency = Currency.objects.create(token_id=0, name="test")
        self.wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency, state=WALLET_STATES.VERIFIED.value)
        self.wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

    def test_transfer_ordering(self):
        Transaction.objects.create(to_wallet=self.wallet1, amount=100)
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                from_wallet=self.wallet2, to_wallet=self.wallet1, amount=10)
        Transaction.objects.create(
            from_wallet=self.wallet1, to_wallet=self.wallet2, amount=20)
        Transaction.objects.create(
            from_wallet=self.wallet2, to_wallet=self.wallet1, amount=10)

    def test_minting_validation(self):
        Transaction.objects.create(to_wallet=self.wallet1, amount=100)
        self.currency.allow_minting = False
        self.currency.save()
        with self.assertRaises(ValidationError):
            Transaction.objects.create(to_wallet=self.wallet1, amount=100)


@skip
class BlockchainSyncTestCase(TestCase):
    def setUp(self):
        self.currency = Currency.objects.create(token_id=0, name="TEZ")
        self.pytezos_client = pytezos.using(
            key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
        self.last_nonce = read_nonce_from_chain(
            self.pytezos_client.key.public_key_hash())

        self.token_contract = self.pytezos_client.contract(
            settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
        self.wallet1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pytezos_client.key.public_key(), currency=self.currency, state=WALLET_STATES.VERIFIED.value)
        self.wallet2 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku3g7CeTEvSKhxipD4Q2B6EiEP8cR323u8PFmGFgKRVRvCneEmT", currency=self.currency, state=WALLET_STATES.VERIFIED.value)
        Transaction.objects.create(to_wallet=self.wallet1, amount=10000)

    def tearDown(self):
        Transaction.objects.all().delete()
        WalletPublicKeyTransferRequest.objects.all().delete()

    def test_wallet_recover_transfer(self):

        Transaction.objects.create(
            from_wallet=self.wallet1, to_wallet=self.wallet2, amount=10)

        Transaction.objects.create(
            from_wallet=self.wallet2, to_wallet=self.wallet1, amount=1)
        WalletPublicKeyTransferRequest.objects.create(
            wallet=self.wallet1, old_public_key=self.wallet1.public_key, new_public_key="edpkvThfdv8Efh1MuqSTUk5EnUFCTjqN6kXDCNXpQ8udN3cKRhNDr2")

        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                from_wallet=self.wallet1, to_wallet=self.wallet2, amount=10)
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                from_wallet=self.wallet2, to_wallet=self.wallet1, amount=1)
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                from_wallet=None, to_wallet=self.wallet1, amount=10)
        with self.assertRaises(ValidationError):
            MetaTransaction.objects.create(
                from_wallet=self.wallet1, to_wallet=self.wallet2, amount=10, nonce=10)
        with self.assertRaises(ValidationError):
            MetaTransaction.objects.create(
                from_wallet=self.wallet2, to_wallet=self.wallet1, amount=1, nonce=10)

        start = time.time()
        self.assertEquals(True, sync_to_blockchain(
            is_dry_run=True))
        end = time.time()
        print(end - start)

    def test_transfer(self):
        for i in range(300):
            Transaction.objects.create(
                from_wallet=self.wallet1, to_wallet=self.wallet2, amount=1)

        start = time.time()
        self.assertEquals(True, sync_to_blockchain(
            is_dry_run=True))
        end = time.time()
        print(end - start)

    @skip
    def test_complex_sync(self):
        for i in range(40):
            key = crypto.Key.generate()
            private_key = key.secret_key()
            public_key = key.public_key()
            user_wallet = Wallet.objects.create(
                public_key=public_key, currency=self.currency, state=WALLET_STATES.VERIFIED.value)
            Transaction.objects.create(
                from_wallet=self.wallet1, to_wallet=user_wallet, amount=10)
            meta_token_transaction = MetaTransaction(
                from_wallet=user_wallet, to_wallet=self.wallet1, nonce=1, amount=1)
            packed_meta_transaction = pack_meta_transaction(
                meta_token_transaction.to_meta_transaction_dictionary())
            signature = key.sign(packed_meta_transaction)
            MetaTransaction.objects.create(
                from_wallet=user_wallet, to_wallet=self.wallet1, signature=signature, nonce=1, amount=1)

            key = crypto.Key.generate()
            public_key = key.public_key()

            WalletPublicKeyTransferRequest.objects.create(
                wallet=user_wallet, old_public_key=user_wallet.public_key, new_public_key=public_key)

        self.assertEquals(81, Transaction.objects.filter(
            state=TRANSACTION_STATES.OPEN.value).count())  # 50 meta, 50 funding, 1 mint
        start = time.time()
        self.assertEquals(True, sync_to_blockchain(
            is_dry_run=False))
        end = time.time()
        self.assertEquals(81, Transaction.objects.filter(
            state=TRANSACTION_STATES.DONE.value).count())
        print(end - start)
