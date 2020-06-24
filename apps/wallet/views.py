from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from rest_framework import generics, mixins, status
from rest_framework.response import Response

from apps.wallet.models import Wallet
from apps.wallet.serializers import (PublicWalletSerializer,
                                     TransactionSerializer, WalletSerializer)


class WalletDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    lookup_field = "walletID"
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    public_serializer = PublicWalletSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        wallet = self.get_object()

        if request.user.is_superuser == True or request.user == wallet.owner:
            pass
            serializer = WalletSerializer(wallet)
        else:
            serializer = PublicWalletSerializer(wallet)

        return Response(serializer.data)


class TransactionDetail(generics.CreateAPIView):
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: other checks needed?
        if self.request.user != serializer.validated_data['from_addr'].owner:
            raise PermissionDenied()

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
