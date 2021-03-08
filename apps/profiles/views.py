import binascii

import pytezos
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, mixins, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.profiles.models import PROFILE_STATES, CompanyProfile, UserProfile
from apps.profiles.serializers import CompanyProfileSerializer, UserProfileSerializer
from apps.verification.models import VERIFICATION_STATES
from apps.wallet.models import Wallet
from project.utils import raise_api_exception


class ProfileCursorPagination(CursorPagination):
    ordering = "created_at"
    page_size = 10
    page_size_query_param = "page_size"


class UserProfileListCreate(generics.ListCreateAPIView):
    serializer_class = UserProfileSerializer
    pagination_class = ProfileCursorPagination

    def get_queryset(self):
        return self.request.user.user_profiles.filter(state=PROFILE_STATES.ACTIVE.value)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["wallet"] = Wallet.objects.get(wallet_id=request.data["wallet"])

        return super().create(request, *args, **kwargs)


class UserProfileDestroy(generics.DestroyAPIView):
    serializer_class = UserProfileSerializer
    pagination_class = ProfileCursorPagination

    def get_queryset(self):
        return self.request.user.user_profiles.filter(state=PROFILE_STATES.ACTIVE.value)


class CompanyProfileListCreate(generics.ListCreateAPIView):
    serializer_class = CompanyProfileSerializer
    pagination_class = ProfileCursorPagination

    def get_queryset(self):
        return self.request.user.company_profiles.filter(
            state=PROFILE_STATES.ACTIVE.value
        )


class CompanyProfileDestroy(generics.DestroyAPIView):
    serializer_class = CompanyProfileSerializer
    pagination_class = ProfileCursorPagination

    def get_queryset(self):
        return self.request.user.company_profiles.filter(
            state=PROFILE_STATES.ACTIVE.value
        )
