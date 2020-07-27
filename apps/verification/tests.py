from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.currency.models import Currency
from apps.verification.models import VERIFICATION_STATES, UserVerification, CompanyVerification
from apps.wallet.models import (WALLET_CATEGORIES, WALLET_STATES,
                                MetaTransaction, Transaction, Wallet)


class VerificationApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")

        self.currency = Currency.objects.create(token_id=0, name="TEZ")
        self.currency_2 = Currency.objects.create(
            token_id=1, name="TEZ2", starting_capital=22)

        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22r", currency=self.currency)

        self.wallet_1_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22q", currency=self.currency)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22f", currency=self.currency, category=WALLET_CATEGORIES.COMPANY.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_2, currency=self.currency)

        self.owner_wallet_1 = Wallet.objects.create(wallet_id=Wallet.generate_wallet_id(
        ), category=WALLET_CATEGORIES.OWNER.value, public_key="edpku976gpuAD2bXyx1XGraeKuCo1gUZ3LAJcHM12W1ecxZwoiu22R", currency=self.currency, state=WALLET_STATES.VERIFIED.value)

        Transaction.objects.create(to_wallet=self.owner_wallet_1, amount=2000)

    def test_different_user_claim(self):
        verification_input = UserVerification.objects.create(
            currency=self.currency, name='testname', address='address1234', telephone_number='123495', date_of_birth='1990-02-18')

        response = self.client.post('/api/verification/verify/'+self.wallet_1.wallet_id, {
            'name': 'testname',
            'address': 'address1234',
            'telephone_number': '123495',
            'date_of_birth': '1990-02-18'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(verification_input.state,
                         VERIFICATION_STATES.OPEN.value)
        self.assertEqual(self.wallet_1.balance, 0)

        self.client.force_authenticate(user=self.user_2)

        response = self.client.post('/api/verification/verify/'+self.wallet_1.wallet_id, {
            'name': 'testname',
            'address': 'address1234',
            'telephone_number': '123495',
            'date_of_birth': '1990-02-18'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(verification_input.state,
                         VERIFICATION_STATES.OPEN.value)
        self.assertEqual(self.wallet_1.balance, 0)

    def test_incorrect_claims(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/verification/verify/'+self.wallet_1_2.wallet_id, {
            'name': 'testname',
            'address': 'address1234',
            'telephone_number': '123495',
            'date_of_birth': '1990-02-18'
        }, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.data, {'detail': 'Verification could not be done, wrong format of body'})
        self.assertEqual(self.wallet_1_2.balance, 0)

        response = self.client.post('/api/verification/verify/'+self.wallet_1.wallet_id, {
            'name': 'testname',
            'owner_name': 'testname',
            'owner_address': 'address1234',
            'owner_telephone_number': '123495',
            'uid': '1990-02-18'
        }, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.data, {'detail': 'Verification could not be done, wrong format of body'})
        self.assertEqual(self.wallet_1.balance, 0)

    def test_new_claim(self):
        start_amount = self.wallet_1.balance

        user_verification_count = UserVerification.objects.all().count()

        self.client.force_authenticate(user=self.user)

        data = {
            'name': 'testname',
            'address': 'address1234',
            'telephone_number': '123495',
            'date_of_birth': '1990-02-18'
        }

        response = self.client.post(
            '/api/verification/verify/'+self.wallet_1.wallet_id, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(
            response.data, {'detail': 'Verification could not be done'})
        self.assertEqual(self.wallet_1.balance, 0)
        self.assertEqual(user_verification_count+1,
                         UserVerification.objects.all().count())

        data['state'] = VERIFICATION_STATES.REQUESTED.value
        self.assertEqual(UserVerification.objects.filter(**data).count(), 1)

    def test_correct_claim(self):
        start_amount = self.wallet_1.balance

        self.client.force_authenticate(user=self.user)

        data = {
            'name': 'testname',
            'address': 'address1234',
            'telephone_number': '123495',
            'date_of_birth': '1990-02-18'
        }

        old_balance = self.wallet_1.balance
        verification_entity = UserVerification(**data)
        verification_entity.currency = self.currency
        verification_entity.save()

        user_verification_count = UserVerification.objects.all().count()

        response = self.client.post(
            '/api/verification/verify/'+self.wallet_1.wallet_id, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            old_balance + self.currency.starting_capital, self.wallet_1.balance)
        self.assertEqual(user_verification_count,
                         UserVerification.objects.all().count())
        data['state'] = VERIFICATION_STATES.CLAIMED.value
        self.assertEqual(UserVerification.objects.filter(**data).count(), 1)

        data_company = {
            'name': 'testname',
            'owner_name': 'testname',
            'owner_address': 'address1234',
            'owner_telephone_number': '123495',
            'uid': '1990-02-18'
        }
        verification_entity_company = CompanyVerification(**data_company)
        verification_entity_company.currency = self.currency
        verification_entity_company.save()
        company_verification_count = CompanyVerification.objects.all().count()
        response = self.client.post(
            '/api/verification/verify/'+self.wallet_1_2.wallet_id, data_company, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(old_balance, self.wallet_1_2.balance)
        self.assertEqual(company_verification_count,
                         CompanyVerification.objects.all().count())
        data_company['state'] = VERIFICATION_STATES.CLAIMED.value
        self.assertEqual(CompanyVerification.objects.filter(
            **data_company).count(), 1)

    def test_double_claim(self):
        start_amount = self.wallet_1.balance

        self.client.force_authenticate(user=self.user)

        data = {
            'name': 'testname',
            'address': 'address1234',
            'telephone_number': '123495',
            'date_of_birth': '1990-02-18'
        }

        old_balance = self.wallet_1.balance
        verification_entity = UserVerification(**data)
        verification_entity.currency = self.currency
        verification_entity.save()

        user_verification_count = UserVerification.objects.all().count()

        response = self.client.post(
            '/api/verification/verify/'+self.wallet_1.wallet_id, data, format='json')
        self.assertEqual(user_verification_count,
                         UserVerification.objects.all().count())
        response_2 = self.client.post(
            '/api/verification/verify/'+self.wallet_1_1.wallet_id, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            old_balance + self.currency.starting_capital, self.wallet_1.balance)
        self.assertEqual(user_verification_count+1,
                         UserVerification.objects.all().count())
        data['state'] = VERIFICATION_STATES.CLAIMED.value
        self.assertEqual(UserVerification.objects.filter(**data).count(), 1)

        self.assertEqual(response_2.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        data['state'] = VERIFICATION_STATES.DOUBLE_CLAIM.value
        self.assertEqual(UserVerification.objects.filter(**data).count(), 1)

    def test_too_many_claims(self):
        self.client.force_authenticate(user=self.user)

        for i in range(self.currency.max_claims):
            data = {
                'name': 'testname'+str(i),
                'address': 'address1234',
                'telephone_number': '123495',
                'date_of_birth': '1990-02-18'
            }
            verification_entity = UserVerification(**data)
            verification_entity.currency = self.currency
            verification_entity.save()

            user_verification_count = UserVerification.objects.all().count()
            old_balance = self.wallet_1.balance

            response = self.client.post(
                '/api/verification/verify/'+self.wallet_1.wallet_id, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                old_balance + self.currency.starting_capital, self.wallet_1.balance)
            self.assertEqual(user_verification_count,
                             UserVerification.objects.all().count())

        data['name'] = 'bla'
        verification_entity = UserVerification(**data)
        verification_entity.currency = self.currency
        verification_entity.save()

        user_verification_count = UserVerification.objects.all().count()
        old_balance = self.wallet_1.balance

        response = self.client.post(
            '/api/verification/verify/'+self.wallet_1.wallet_id, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(old_balance, self.wallet_1.balance)
        self.assertEqual(
            response.data, {'detail': f'You can not claim more than {self.currency.max_claims} times'})
        self.assertEqual(user_verification_count,
                         UserVerification.objects.all().count())

        data['state'] = VERIFICATION_STATES.CLAIM_LIMIT_REACHED.value
        self.assertEqual(UserVerification.objects.filter(**data).count(), 1)
