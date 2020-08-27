from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.currency.models import Currency
from apps.verification.models import VERIFICATION_STATES, UserVerification, CompanyVerification, SMSPinVerification, AddressPinVerification
from apps.wallet.models import (WALLET_CATEGORIES, WALLET_STATES,
                                MetaTransaction, Transaction, Wallet)
from apps.profiles.models import UserProfile, CompanyProfile
from django.conf import settings


class ProfileApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNg'

    def setUp(self):
        settings.DEBUG = True
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

        Transaction.objects.create(
            to_wallet=self.currency.owner_wallet, amount=2000)
        Transaction.objects.create(
            to_wallet=self.currency_2.owner_wallet, amount=2000)

    def tearDown(self):
        settings.DEBUG = False

    def test_user_profile_verification_flow(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24"
        )

        data = {
            "first_name": "Alessandro",
            "last_name": "De Carli",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "telephone_number": "+41763057500",
            "date_of_birth": "1989-06-24",
            "wallet": self.wallet_1.wallet_id
        }
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(user_verification.state,
                         VERIFICATION_STATES.OPEN.value)
        self.assertEqual(self.wallet_1.balance, 0)

        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        data['wallet'] = self.wallet_2.wallet_id
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.user)
        data['wallet'] = self.wallet_1_2.wallet_id
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        data['wallet'] = self.wallet_1.wallet_id
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        # the second create overrides user 2
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data['verification_stage'], 1)

        user_verification = UserVerification.objects.get(
            pk=user_verification.pk)
        self.assertEqual(user_verification.state,
                         VERIFICATION_STATES.PENDING.value)
        self.assertEqual(self.wallet_1.balance, 0)

        user_profile = UserProfile.objects.get(pk=response.data['uuid'])
        sms_pin_verification = user_profile.sms_pin_verification

        self.assertEqual(sms_pin_verification.state,
                         VERIFICATION_STATES.PENDING.value)

        self.client.force_authenticate(user=self.user_2)

        # TODO: shouldn't test for those endpoints be inside apps.verification.tests ?
        response = self.client.post(
            '/api/verification/resend_user_profile_pin/{}'.format(user_profile.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            '/api/verification/resend_user_profile_pin/{}'.format(user_profile.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.post(
            '/api/verification/verify_user_profile_pin/{}'.format(user_profile.pk), {'pin': 'WRONG'}, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        user_profile = UserProfile.objects.get(pk=user_profile.pk)
        pin = user_profile.sms_pin_verification.pin

        response = self.client.post(
            '/api/verification/verify_user_profile_pin/{}'.format(user_profile.pk), {'pin': pin}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.post(
            '/api/verification/resend_user_profile_pin/{}'.format(user_profile.pk), data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        user_verification.refresh_from_db()
        self.assertEqual(user_verification.state,
                         VERIFICATION_STATES.CLAIMED.value)
        sms_pin_verification = SMSPinVerification.objects.get(
            pk=user_profile.sms_pin_verification.pk)
        self.assertEqual(sms_pin_verification.state,
                         VERIFICATION_STATES.CLAIMED.value)

        self.wallet_1.refresh_from_db()
        self.assertEqual(self.wallet_1.balance, 10)
        self.assertEqual(self.wallet_1.state, WALLET_STATES.VERIFIED.value)

        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cannot reuse burned verification
        self.assertEqual(response.data['verification_stage'], 0)

    def test_company_profile_verification_flow(self):
        company_verification = CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3"
        )

        data = {
            "name": "Papers AG",
            "uid": "12-3-4-3",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1.wallet_id
        }

        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(company_verification.state,
                         VERIFICATION_STATES.OPEN.value)
        self.assertEqual(self.wallet_1.balance, 0)

        self.client.force_authenticate(user=self.user_2)

        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        data['wallet'] = self.wallet_2.wallet_id
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        self.client.force_authenticate(user=self.user)

        data['wallet'] = self.wallet_1.wallet_id
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        data['wallet'] = self.wallet_1_2.wallet_id
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        # the second create overrides user 2
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data['verification_stage'], 1)

        company_verification = CompanyVerification.objects.get(
            pk=company_verification.pk)
        self.assertEqual(company_verification.state,
                         VERIFICATION_STATES.PENDING.value)
        self.assertEqual(self.wallet_1_2.balance, 0)

        company_profile = CompanyProfile.objects.get(pk=response.data['uuid'])
        address_pin_verification = company_profile.address_pin_verification

        self.assertEqual(address_pin_verification.state,
                         VERIFICATION_STATES.PENDING.value)

        self.client.force_authenticate(user=self.user_2)

        response = self.client.post(
            '/api/verification/verify_company_profile_pin/{}'.format(company_profile.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            '/api/verification/verify_company_profile_pin/{}'.format(company_profile.pk), {'pin': 'WRONG'}, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        company_profile.refresh_from_db()
        pin = company_profile.address_pin_verification.pin

        response = self.client.post(
            '/api/verification/verify_company_profile_pin/{}'.format(company_profile.pk), {'pin': pin}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        company_verification = CompanyVerification.objects.get(
            pk=company_verification.pk)
        self.assertEqual(company_verification.state,
                         VERIFICATION_STATES.CLAIMED.value)
        address_pin_verification = AddressPinVerification.objects.get(
            pk=company_profile.address_pin_verification.pk)
        self.assertEqual(address_pin_verification.state,
                         VERIFICATION_STATES.CLAIMED.value)
        self.wallet_1_2.refresh_from_db()
        self.assertEqual(self.wallet_1_2.balance, 0)
        self.assertEqual(self.wallet_1_2.state, WALLET_STATES.VERIFIED.value)

        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # cannot reuse burned verification
        self.assertEqual(response.data['verification_stage'], 0)

    def test_user_profile_destroy(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24"
        )

        data = {
            "first_name": "Alessandro",
            "last_name": "De Carli",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "telephone_number": "+41763057500",
            "date_of_birth": "1989-06-24",
            "wallet": self.wallet_2.wallet_id
        }

        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_2_profile_uuid = response.data['uuid']

        self.client.force_authenticate(user=self.user)
        data['wallet'] = self.wallet_1.wallet_id
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_1_profile_uuid = response.data['uuid']

        response = self.client.delete(
            '/api/profiles/user_profiles/{}/'.format(user_2_profile_uuid), data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)
        # we did not delete, because it's the wrong user
        self.assertEqual(UserProfile.objects.all().count(), 2)

        response = self.client.delete(
            '/api/profiles/user_profiles/{}/'.format(user_1_profile_uuid), data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserProfile.objects.all().count(), 1)

    def test_company_profile_verification_flow(self):
        company_verification = CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3"
        )

        data = {
            "name": "Papers AG",
            "uid": "12-3-4-3",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/profiles/company_profiles/', data, format='json')
        # the second create overrides user 2

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_1_profile_uuid = response.data['uuid']

        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(
            '/api/profiles/company_profiles/{}/'.format(user_1_profile_uuid), data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)
        # we did not delete, because it's the wrong user
        self.assertEqual(CompanyProfile.objects.all().count(), 1)

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            '/api/profiles/company_profiles/{}/'.format(user_1_profile_uuid), data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_204_NO_CONTENT)
        self.assertEqual(CompanyProfile.objects.all().count(), 0)
