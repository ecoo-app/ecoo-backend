import time
from unittest import skip

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.currency.models import Currency
from apps.profiles.models import (PROFILE_VERIFICATION_STAGES, CompanyProfile,
                                  UserProfile)
from apps.verification.models import (VERIFICATION_STATES,
                                      AddressPinVerification,
                                      CompanyVerification, PlaceOfOrigin,
                                      SMSPinVerification, UserVerification)
from apps.wallet.models import (WALLET_CATEGORIES, WALLET_STATES,
                                MetaTransaction, Transaction, Wallet)


class ProfileApiTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkv75x1Rn8GZbGUU8eXqyur5sWxdJNazCq3eN4SW6J4ykp2XUNgC'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")

        self.currency = Currency.objects.create(
            token_id=0, name="TEZ", symbol='tez', claim_deadline='2120-01-01', campaign_end='2120-01-01')
        self.currency_2 = Currency.objects.create(
            token_id=1, name="TEZ2", starting_capital=22, symbol='tez2', claim_deadline='2120-01-01', campaign_end='2120-01-01')

        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuWW8CKkKRD7VipUyggFFnUaCumbMKDBLzPRNtbDx9zG2PtMeRS", currency=self.currency)

        self.wallet_1_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuqDMtBwt45prqmLpjUTNNKUkKvy7i1xXvEkkHkDfAq6ihzMGtX", currency=self.currency)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuUwKji4CWfQchkf2F1X8VKbYXtgjarAmg7pn4Rhydf1YYzrDka", currency=self.currency, category=WALLET_CATEGORIES.COMPANY.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_2, currency=self.currency)

        Transaction.objects.create(
            to_wallet=self.currency.owner_wallet, amount=2000)
        Transaction.objects.create(
            to_wallet=self.currency_2.owner_wallet, amount=2000)

    def test_user_profile_verification_flow(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24"
        )

        PlaceOfOrigin.objects.create(
            place_of_origin="Baden AG", user_verification=user_verification)

        data = {
            "first_name": "Alessandro",
            "last_name": "De Carli",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "telephone_number": "+41763057500",
            "date_of_birth": "1989-06-24",
            "wallet": self.wallet_1.wallet_id,
            "place_of_origin": "Baden AG"
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
        self.assertEqual(response.json()[
                         'detail'][0], "You are retrying too fast, please wait for 14 seconds")

        time.sleep(15)

        response = self.client.post(
            '/api/verification/verify_user_profile_pin/{}'.format(user_profile.pk), {'pin': 'WRONG'}, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        user_profile = UserProfile.objects.get(pk=user_profile.pk)
        pin = user_profile.sms_pin_verification.pin
        sms_pin_verification = SMSPinVerification.objects.get(
            pk=user_profile.sms_pin_verification.pk)

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

        sms_pin_verification.refresh_from_db()
        self.assertEqual(sms_pin_verification.state,
                         VERIFICATION_STATES.CLAIMED.value)

        self.wallet_1.refresh_from_db()
        self.assertEqual(self.wallet_1.balance, 10)
        self.assertEqual(self.wallet_1.state, WALLET_STATES.VERIFIED.value)

        # cannot reuse burned verification
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

        # cannot reuse burned verification
        # self.assertEqual(response.data['verification_stage'], 0)

    def test_company_verification_ok(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr"
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
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['verification_stage'],
                         PROFILE_VERIFICATION_STAGES.PARTIALLY_VERIFIED.value)
        # verify with pin
        company_profile = CompanyProfile.objects.get(pk=response.data['uuid'])
        address_pin_verification = company_profile.address_pin_verification
        self.assertIsNotNone(address_pin_verification)

        pin = company_profile.address_pin_verification.pin
        response = self.client.post(
            '/api/verification/verify_company_profile_pin/{}'.format(company_profile.pk), {'pin': pin}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(company_profile.verification_stage(),
                         PROFILE_VERIFICATION_STAGES.VERIFIED.value)

    def test_company_verification_not_matching_wallet(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr"
        )

        data = {
            "name": "Papers AG",
            "uid": "12-3-4-3",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_company_verification_incomplete_address(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
        )

        data = {
            # "name": "Papers AG",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            "name": "Papers AG",
            # "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            "name": "Papers AG",
            "address_street": "Sonnmattstr. 121",
            # "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            "name": "Papers AG",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            # "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_company_verification_no_uid(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr"
        )

        data = {
            "name": "Papers AG",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['verification_stage'], PROFILE_VERIFICATION_STAGES.UNVERIFIED.value)
        company_profile = CompanyProfile.objects.get(pk=response.data['uuid'])

        # TODO: check that no verification data is there!!

        try:
            _ = company_profile.address_pin_verification
        except ObjectDoesNotExist:
            pass

        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr"
        )

        # same data again
        data = {
            "name": "Papers AG",
            # "uid": "",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)
        # self.assertEqual(
        # response.data['verification_stage'], PROFILE_VERIFICATION_STAGES.UNVERIFIED.value)
        # company_profile = CompanyProfile.objects.get(pk=response.data['uuid'])
        # try:
        # address_pin_verification = company_profile.address_pin_verification
        # except ObjectDoesNotExist:
        # pass

    def test_company_verification_not_matching_address(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-4",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
        )

        data = {
            "name": "Papers AG",
            "uid": "12-3-4-3",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "wallet": self.wallet_1.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_422_UNPROCESSABLE_ENTITY)

    # FIXME: this wasn't run through anymore because of a test with the same name futher down now named .._2
    @skip
    def test_company_profile_verification_flow(self):
        company_verification = CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr"
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
        UserVerification.objects.create(
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
            "wallet": self.wallet_2.wallet_id,
            "place_of_origin": "Baden AG"
        }

        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # TODO: why is this failing
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

    def test_company_profile_verification_flow_2(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_town="Birr",
            address_postal_code="5242"
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
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
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

    def test_invalid_postal_code(self):
        CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_town="Birr",
            address_postal_code="5242"
        )

        data = {
            "name": "Papers AG",
            "uid": "12-3-4-3",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "ab",
            "address_town": "Birr",
            "wallet": self.wallet_1_2.wallet_id
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')
        # the second create overrides user 2
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        UserVerification.objects.create(
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
            "address_postal_code": "ab",
            "address_town": "Birr",
            "telephone_number": "+41763057500",
            "date_of_birth": "1989-06-24",
            "wallet": self.wallet_2.wallet_id,
            "place_of_origin": "Baden AG"
        }

        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_verification_with_different_place_of_origin(self):
        self.client.force_authenticate(user=self.user)
        user_verification = UserVerification.objects.create(
            first_name="Alessandro",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            # place_of_origin="Baden AG"
        )

        PlaceOfOrigin.objects.create(
            user_verification=user_verification, place_of_origin="Baden AG")
        PlaceOfOrigin.objects.create(
            user_verification=user_verification, place_of_origin="Zürich ZH")

        data = {
            "first_name": "Alessandro",
            "last_name": "De Carli",
            "address_street": "Sonnmattstr. 121",
            "address_postal_code": "5242",
            "address_town": "Birr",
            "telephone_number": "+41763057500",
            "date_of_birth": "1989-06-24",
            "wallet": self.wallet_1.wallet_id,
            "place_of_origin": "Baden ZH",
        }

        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_profile = UserProfile.objects.get(
            pk=response.data['uuid'])

        # correct place of origin
        data['place_of_origin'] = "Baden AG  "

        response = self.client.post(
            '/api/profiles/user_profiles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_profile = UserProfile.objects.get(
            pk=response.data['uuid'])
        pin = user_profile.sms_pin_verification
        response = self.client.post(
            '/api/verification/verify_user_profile_pin/{}'.format(user_profile.pk), {'pin': pin.pin}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user_verification = UserVerification.objects.get(
            pk=user_verification.pk)
        self.assertEqual(user_verification.state,
                         VERIFICATION_STATES.CLAIMED.value)

    @skip
    def test_to_many_verifications_company(self):
        self.client.force_authenticate(user=self.user)

        for i in range(5):
            company_verification = CompanyVerification.objects.create(
                name="Papers AG" + str(i),
                uid="12-3-4-3"
            )

            data = {
                "name": "Papers AG" + str(i),
                "uid": "12-3-4-3",
                "address_street": "Sonnmattstr. 121",
                "address_postal_code": "5242",
                "address_town": "Birr",
                "wallet": self.wallet_1_2.wallet_id
            }

            response = self.client.post(
                '/api/profiles/company_profiles/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            company_profile = CompanyProfile.objects.get(
                pk=response.data['uuid'])
            pin = company_profile.address_pin_verification
            response = self.client.post(
                '/api/verification/verify_company_profile_pin/{}'.format(company_profile.pk), {'pin': pin.pin}, format='json')
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            company_verification = CompanyVerification.objects.get(
                pk=company_verification.pk)
            self.assertEqual(company_verification.state,
                             VERIFICATION_STATES.CLAIMED.value)

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
        response = self.client.post(
            '/api/profiles/company_profiles/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        company_profile = CompanyProfile.objects.get(pk=response.data['uuid'])
        pin = company_profile.address_pin_verification
        response = self.client.post('/api/verification/verify_company_profile_pin/{}'.format(
            company_profile.pk), {'pin': pin.pin}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        company_verification = CompanyVerification.objects.get(
            pk=company_verification.pk)
        self.assertNotEqual(company_verification.state,
                            VERIFICATION_STATES.CLAIMED.value)

    @skip
    def test_to_many_verifications_user(self):
        self.client.force_authenticate(user=self.user)

        for i in range(5):
            user_verification = UserVerification.objects.create(
                first_name="Alessandro" + str(i),
                last_name="De Carli",
                address_street="Sonnmattstr. 121",
                address_postal_code="5242",
                address_town="Birr",
                date_of_birth="1989-06-24"
            )

            data = {
                "first_name": "Alessandro" + str(i),
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
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            user_profile = UserProfile.objects.get(
                pk=response.data['uuid'])
            pin = user_profile.sms_pin_verification
            response = self.client.post(
                '/api/verification/verify_user_profile_pin/{}'.format(user_profile.pk), {'pin': pin.pin}, format='json')
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            user_verification = UserVerification.objects.get(
                pk=user_verification.pk)
            self.assertEqual(user_verification.state,
                             VERIFICATION_STATES.CLAIMED.value)

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_profile = UserProfile.objects.get(pk=response.data['uuid'])
        pin = user_profile.sms_pin_verification
        response = self.client.post('/api/verification/verify_user_profile_pin/{}'.format(
            user_profile.pk), {'pin': pin.pin}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user_verification = UserVerification.objects.get(
            pk=user_verification.pk)
        self.assertNotEqual(user_verification.state,
                            VERIFICATION_STATES.CLAIMED.value)


class ProfileLookupTest(APITestCase):
    pubkey_1 = 'edpkuvNy6TuQ2z8o9wnoaTtTXkzQk7nhegCHfxBc4ecsd4qG71KYNG'
    pubkey_2 = 'edpkv75x1Rn8GZbGUU8eXqyur5sWxdJNazCq3eN4SW6J4ykp2XUNgC'

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")
        self.user_2 = get_user_model().objects.create(
            username="testuser_2", password="abcd")

        self.currency = Currency.objects.create(
            token_id=0, name="TEZ", symbol='tez', claim_deadline='2120-01-01', campaign_end='2120-01-01')
        self.currency_2 = Currency.objects.create(
            token_id=1, name="TEZ2", starting_capital=22, symbol='tez2', claim_deadline='2120-01-01', campaign_end='2120-01-01')

        self.wallet_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuWW8CKkKRD7VipUyggFFnUaCumbMKDBLzPRNtbDx9zG2PtMeRS", currency=self.currency)

        self.wallet_1_1 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuqDMtBwt45prqmLpjUTNNKUkKvy7i1xXvEkkHkDfAq6ihzMGtX", currency=self.currency)

        self.wallet_1_2 = Wallet.objects.create(owner=self.user, wallet_id=Wallet.generate_wallet_id(
        ), public_key="edpkuUwKji4CWfQchkf2F1X8VKbYXtgjarAmg7pn4Rhydf1YYzrDka", currency=self.currency, category=WALLET_CATEGORIES.COMPANY.value)

        self.wallet_2 = Wallet.objects.create(owner=self.user_2, wallet_id=Wallet.generate_wallet_id(
        ), public_key=self.pubkey_2, currency=self.currency)

        Transaction.objects.create(
            to_wallet=self.currency.owner_wallet, amount=2000)
        Transaction.objects.create(
            to_wallet=self.currency_2.owner_wallet, amount=2000)

    def test_user_complete(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )

        PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )

        UserProfile.objects.create(
            owner=self.user,
            first_name='Alessandro', last_name='De Carli', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.PENDING.value)

    def test_first_names1(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro Lionel",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )

        PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )

        UserProfile.objects.create(
            owner=self.user,
            first_name='Lionel', last_name='De Carli', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.PENDING.value)

    def test_first_names2(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro Lionel",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )

        PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )

        UserProfile.objects.create(
            owner=self.user,
            first_name='Lionel Alessandro', last_name='De Carli', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.PENDING.value)

    def test_first_names3(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro Lionel",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )

        PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )

        UserProfile.objects.create(
            owner=self.user,
            first_name='Lionel Alessandro Markus', last_name='De Carli', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.OPEN.value)

    @skip('Not implemented yet')
    def test_last_names(self):
        user_verification = UserVerification.objects.create(
            first_name="Alessandro",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )

        PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )

        UserProfile.objects.create(
            owner=self.user,
            first_name='Alessandro', last_name='Carli', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.PENDING.value)

    def test_company_lookup(self):
        company_verification = CompanyVerification.objects.create(
            name="Papers AG",
            uid="12-3-4-3",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr"
        )

        CompanyProfile.objects.create(
            owner=self.user,
            name='bla',
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            phone_number='+41783285325',
            wallet=self.wallet_1_2,
            uid='12-3-4-3'
        )

        company_verification.refresh_from_db()
        self.assertEquals(company_verification.state,
                          VERIFICATION_STATES.PENDING.value)

    def test_empty_names(self):
        # completely empty names are prohibited by the model!

        user_verification = UserVerification.objects.create(
            first_name="Alessandro Lionel",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
        )

        PlaceOfOrigin.objects.create(
            place_of_origin='Baden AG',
            user_verification=user_verification
        )

        UserProfile.objects.create(
            owner=self.user,
            first_name=' ', last_name='De Carli', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.OPEN.value)

        UserProfile.objects.create(
            owner=self.user,
            first_name='Alessandro Lionel', last_name=' ', address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin='Baden AG',
            telephone_number='+41783285325',
            wallet=self.wallet_1)

        user_verification.refresh_from_db()
        self.assertEquals(user_verification.state,
                          VERIFICATION_STATES.OPEN.value)
