from django_filters.rest_framework import DjangoFilterBackend
from project.utils import raise_api_exception
import binascii

import pytezos
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from rest_framework import generics, mixins, status, filters
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import BasePermission

from apps.profiles.serializers import UserProfileSerializer, CompanyProfileSerializer, AutocompleteUserSerializer, AutocompleteCompanySerializer
from apps.profiles.models import UserProfile, CompanyProfile

class UserProfileListCreate(generics.ListCreateAPIView):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return self.request.user.user_profiles


class UserProfileDestroy(generics.DestroyAPIView):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return self.request.user.user_profiles


class CompanyProfileListCreate(generics.ListCreateAPIView):
    serializer_class = CompanyProfileSerializer

    def get_queryset(self):
        return self.request.user.company_profiles


class CompanyProfileDestroy(generics.DestroyAPIView):
    serializer_class = CompanyProfileSerializer

    def get_queryset(self):
        return self.request.user.company_profiles


class AutocompleteUserList(generics.ListCreateAPIView):
    serializer_class = AutocompleteUserSerializer

    def list(self, request):
        self.request = request
        return super(AutocompleteUserList, self).list(request)

    def get_queryset(self):
        search_string = self.request.GET['search']
        if search_string.strip() == '':
            return UserProfile.objects.none()
        return UserProfile.objects.filter(Q(address_street__istartswith=search_string) & (Q(user_verification__state=0) | Q(user_verification__isnull=True))).values('address_street', 'address_postal_code').distinct('address_street', 'address_postal_code')

        
class AutocompleteCompanyList(generics.ListCreateAPIView):
    serializer_class = AutocompleteCompanySerializer

    def list(self, request):
        self.request = request
        return super(AutocompleteCompanyList, self).list(request)

    def get_queryset(self):
        search_string = self.request.GET['search']
        if search_string.strip() == '':
            return CompanyProfile.objects.none()
        return CompanyProfile.objects.filter(Q(address_street__istartswith=search_string) & (Q(company_verification__state=0) | Q(company_verification__isnull=True))).values('address_street', 'address_postal_code').distinct('address_street', 'address_postal_code')
