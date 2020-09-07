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

from apps.profiles.serializers import UserProfileSerializer, CompanyProfileSerializer
from apps.profiles.models import UserProfile, CompanyProfile
from django.utils.translation import ugettext_lazy as _
from apps.wallet.models import Wallet


# TODO: add check for too many profiles per user

class UserProfileListCreate(generics.ListCreateAPIView):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return self.request.user.user_profiles

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['wallet'] = Wallet.objects.get(wallet_id=request.data['wallet'])

        return super().create(request, *args, **kwargs)


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
