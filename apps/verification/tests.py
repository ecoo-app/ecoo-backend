from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from apps.verification.models import UserVerification, CompanyVerification
from django.conf import settings


USER_AUTOCOMPLETE_ENDPOINT  = '/api/verification/autocomplete_user/'
COMPANY_AUTOCOMPLETE_ENDPOINT  = '/api/verification/autocomplete_company/'

class VerificationApiTest(APITestCase):

    def setUp(self):
        settings.DEBUG = True
        self.user = get_user_model().objects.create(
            username="testuser", password="abcd")

        UserVerification.objects.create(first_name='abc', last_name='def', address_street='testStreet 1', address_town='town1', address_postal_code='123', date_of_birth='2019-12-12')
        UserVerification.objects.create(first_name='abc', last_name='def', address_street='tustStreet 1', address_town='test1', address_postal_code='123', date_of_birth='2019-12-12')
        UserVerification.objects.create(first_name='abc', last_name='def', address_street='tuststreet 2', address_town='test1', address_postal_code='123', date_of_birth='2019-12-12')

        CompanyVerification.objects.create(name='abc', uid='def', address_street='testStreet 1', address_town='town1', address_postal_code='123')
        CompanyVerification.objects.create(name='abc', uid='def', address_street='tustStreet 1', address_town='test1', address_postal_code='123')
        CompanyVerification.objects.create(name='abc', uid='def', address_street='tuststreet 2', address_town='test1', address_postal_code='123')
       

    def test_empty_query(self):
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT + '', {'search': ''})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(COMPANY_AUTOCOMPLETE_ENDPOINT + '', {'search': ''})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT , {'search': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])
        
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT , {'search': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])
        

    def test_no_result_user(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT , {'search': 'abc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_one_result_user(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT , {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['address_street'], 'testStreet 1')

    def test_two_result_user(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT , {'search': 'tusts'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['address_street'], 'tustStreet 1')
        self.assertEqual(response.data['results'][1]['address_street'], 'tuststreet 2')

    def test_multiple_result_user(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(USER_AUTOCOMPLETE_ENDPOINT , {'search': 'T'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['address_street'], 'testStreet 1')
        self.assertEqual(response.data['results'][1]['address_street'], 'tustStreet 1')
        self.assertEqual(response.data['results'][2]['address_street'], 'tuststreet 2')
    
    
    def test_no_result_company(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(COMPANY_AUTOCOMPLETE_ENDPOINT , {'search': 'abc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_one_result_company(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(COMPANY_AUTOCOMPLETE_ENDPOINT , {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['address_street'], 'testStreet 1')

    def test_two_result_company(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(COMPANY_AUTOCOMPLETE_ENDPOINT , {'search': 'tust'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['address_street'], 'tustStreet 1')
        self.assertEqual(response.data['results'][1]['address_street'], 'tuststreet 2')

    def test_multiple_result_company(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(COMPANY_AUTOCOMPLETE_ENDPOINT , {'search': 'T'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['address_street'], 'testStreet 1')
        self.assertEqual(response.data['results'][1]['address_street'], 'tustStreet 1')
        self.assertEqual(response.data['results'][2]['address_street'], 'tuststreet 2')

