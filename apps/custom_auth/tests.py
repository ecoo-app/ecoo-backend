from django.contrib.auth import get_user_model
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.custom_auth.serializers import ApplicationSerializer


class CustomAuthTest(APITestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(email='abc@abc.ch',
                                                                   username="testuser", password="abcd", )
        pass

    def test_application_endpoint(self):
        app = Application.objects.create(
            name='test_name', client_type="public", authorization_grant_type="password", user=self.superuser)

        response = self.client.get('/api/auth/applications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([ApplicationSerializer(app).data],
                         response.data['results'])
