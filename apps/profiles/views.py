from django.utils.translation import ugettext_lazy as _
from rest_framework import generics
from rest_framework.pagination import CursorPagination

from apps.profiles.models import PROFILE_STATES
from apps.profiles.serializers import CompanyProfileSerializer, UserProfileSerializer
from apps.wallet.models import Wallet


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
