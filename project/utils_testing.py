from apps.currency.models import Currency
from apps.verification.models import (VERIFICATION_STATES, CompanyVerification,
                                      PlaceOfOrigin, UserVerification)
from apps.wallet.models import (WALLET_CATEGORIES, WALLET_STATES,
                                CashOutRequest, MetaTransaction, PaperWallet,
                                Transaction, Wallet,
                                WalletPublicKeyTransferRequest)
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APIRequestFactory, APITestCase


class BaseEcouponApiTestCase(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")
        self.currency = Currency.objects.create(
            token_id=0, name="TEZ", symbol='tez', claim_deadline='2120-01-01', campaign_end='2120-01-01')
        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency, state=WALLET_STATES.VERIFIED.value)
        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuSwJiAs2HdRopJwuaoSFKPbSPFAaXLGjT4Hjthc3UeXeign2w6", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkutu49fgbHxV6vdVRBLbvCLpuq7CmSR6pnowxZRFcY7c76wUqHT", currency=self.currency, state=WALLET_STATES.VERIFIED.value)
        
        user_verification = UserVerification.objects.create(
            first_name="Alessandro11",
            last_name="De Carli11",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )        
        place_of_origin = PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )
        self.paper_wallet = PaperWallet.generate_new_wallet(self.currency, place_of_origin, user_verification )
        
        self.currency.cashout_wallet = self.wallet_2
        self.currency.save()
