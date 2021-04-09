from django.urls.base import reverse
from rest_framework.test import APITestCase

from apps.profiles.models import CompanyProfile, UserProfile
from apps.verification.models import VERIFICATION_STATES, SMSPinVerification
from project.utils_testing import EcouponTestCaseMixin


class SmsVerificationApiTest(EcouponTestCaseMixin, APITestCase):
    def test_create_sms_verification_user(self):
        profile = UserProfile.objects.create(
            owner=self.user,
            first_name="Alessandro234",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin="Baden AG",
            telephone_number="+41783285325",
            wallet=self.wallet_1,
        )
        sms_verification_count = SMSPinVerification.objects.all().count()

        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count + 1
        )

        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 304)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count + 1
        )

    def test_create_sms_verification_user_wrong_profile(self):
        profile = UserProfile.objects.create(
            owner=self.user_2,
            first_name="Alessandro234",
            last_name="De Carli",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            date_of_birth="1989-06-24",
            place_of_origin="Baden AG",
            telephone_number="+41783285325",
            wallet=self.wallet_2,
        )
        sms_verification_count = SMSPinVerification.objects.all().count()

        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count
        )

    def test_create_sms_verification_company(self):
        profile = CompanyProfile.objects.create(
            owner=self.user,
            name="bla",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            telephone_number="+41783285325",
            wallet=self.wallet_1_2,
            uid="12-3-4-3",
        )
        sms_verification_count = SMSPinVerification.objects.all().count()

        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count + 1
        )

        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 304)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count + 1
        )

    def test_create_sms_verification_company_wrong_profile(self):
        profile = CompanyProfile.objects.create(
            owner=self.user,
            name="bla",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            telephone_number="+41783285325",
            wallet=self.wallet_1_2,
            uid="12-3-4-3",
        )
        sms_verification_count = SMSPinVerification.objects.all().count()

        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
            # "/api/verification/create_and_send_sms_pin/{}".format(profile.pk)
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count
        )
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            reverse("verification:create_sms_pin", args=[profile.pk]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            SMSPinVerification.objects.all().count(), sms_verification_count
        )

    def test_resent_company_profile_pin(self):
        profile = CompanyProfile.objects.create(
            owner=self.user,
            name="bla",
            address_street="Sonnmattstr. 121",
            address_postal_code="5242",
            address_town="Birr",
            telephone_number="+41783285325",
            wallet=self.wallet_1_2,
            uid="12-3-4-3",
        )

        sms_verification = SMSPinVerification.objects.create(
            company_profile=profile, pin="1234", state=VERIFICATION_STATES.PENDING.value
        )

        response = self.client.post(
            reverse("verification:resend_company_profile_pin", args=[profile.pk])
        )
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            reverse("verification:resend_company_profile_pin", args=[profile.pk])
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("verification:resend_company_profile_pin", args=[profile.pk])
        )
        self.assertEqual(response.status_code, 204)

        sms_verification.state = VERIFICATION_STATES.CLAIMED.value
        sms_verification.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("verification:resend_company_profile_pin", args=[profile.pk])
        )
        self.assertEqual(response.status_code, 422)
