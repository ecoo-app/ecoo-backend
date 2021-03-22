from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls.base import reverse
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APITestCase

from apps.custom_auth.serializers import ApplicationSerializer
from project.utils_testing import EcouponTestCaseMixin


class CustomAuthTest(APITestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            email="abc@abc.ch",
            username="testuser",
            password="abcd",
        )
        pass

    def test_application_endpoint(self):
        app = Application.objects.create(
            name="test_name",
            client_type="public",
            authorization_grant_type="password",
            user=self.superuser,
        )

        response = self.client.get("/api/auth/applications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([ApplicationSerializer(app).data], response.data["results"])


class LoginTestCase(EcouponTestCaseMixin, TestCase):
    def test_login_working(self):

        normal_user_data = {"username": "testuser", "password": "abcd"}
        staff_user_data = {"username": "staff1", "password": "staff1"}

        for data in [normal_user_data, staff_user_data]:
            self.client.logout()
            resp = self.client.post(
                reverse("token_obtain_pair"), data=data, format="json"
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("access", resp.data)
            self.assertIn("refresh", resp.data)
