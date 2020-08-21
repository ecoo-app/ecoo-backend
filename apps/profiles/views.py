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

from apps.profiles.serializers import UserProfileSerializer, CompanyProfileSerializer, AutocompleteSerializer
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


class AutocompleteListCreate(generics.ListCreateAPIView):
    serializer_class = AutocompleteSerializer

    def list(self, request):
        self.request = request
        return super(AutocompleteListCreate, self).list(request)

    def get_queryset(self):
        search_string = self.request.GET['search']
        if search_string.strip() == '':
            return UserProfile.objects.none()
        return UserProfile.objects.filter(Q(user_verification__state=0) |Q(user_verification__isnull=True)).filter(Q(address_street__istartswith=search_string) | Q(address_town__istartswith=search_string) | Q(address_postal_code__istartswith=search_string))