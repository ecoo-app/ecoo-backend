from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from rest_framework import generics, mixins, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from apps.wallet.models import TokenTransaction, Wallet
from apps.wallet.serializers import (PublicWalletSerializer,
                                     TransactionSerializer, WalletSerializer)
from apps.wallet.utils import CustomCursorPagination
from pytezos import Key

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


class WalletList(generics.ListAPIView):
    serializer_class = WalletSerializer

    def get_queryset(self):
        return Wallet.getBelongingToUser(self.request.user)


class TransactionDetail(generics.CreateAPIView):
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if self.request.user != serializer.validated_data['from_addr'].owner:
            raise PermissionDenied()
        
        from_address = serializer.validated_data['from_addr'].address

        pk = Key.from_encoded_key(from_address)
        # TODO: exchange TEST with the message to test for! 
        if pk.verify(self.request.data.get('signature'), 'test') != None:
            e = APIException()
            e.status_code = 422
            e.detail = 'Signature is invalid'
            raise e

        if self.request.data.get('nonce') - serializer.validated_data['from_addr'].nonce != 1:
            e = APIException()
            e.status_code = 422
            e.detail = 'Nonce value is incorrect'
            raise e

        # try:

        obj = serializer.save()
        headers = self.get_success_headers(serializer.data)

        obj.from_addr.nonce += 1
        obj.from_addr.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TransactionList(generics.ListAPIView):
    # TODO: different serializer??
    serializer_class = TransactionSerializer
    filterset_fields = ['from_addr__walletID', 'to_addr__walletID', 'amount']
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        if self.request.user.is_superuser:
            return TokenTransaction.objects.all()
        return TokenTransaction.getBelongingToUser(self.request.user)
