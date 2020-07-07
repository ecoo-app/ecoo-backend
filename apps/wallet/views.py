from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from rest_framework import generics, mixins, status
from rest_framework.response import Response

from apps.wallet.models import Wallet, TokenTransaction
from apps.wallet.serializers import (PublicWalletSerializer,
                                     TransactionSerializer, WalletSerializer)
from apps.wallet.utils import CustomCursorPagination
from rest_framework.exceptions import APIException, ValidationError

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
    



class TransactionDetail(generics.CreateAPIView):
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if self.request.user != serializer.validated_data['from_addr'].owner:
            raise PermissionDenied()

        # TODO: check signature
        if self.request.data.get('nonce') - serializer.validated_data['from_addr'].nonce != 1:
            e = APIException()
            e.status_code = 422
            e.detail = 'Nonce value is incorrect'
            raise e
        
        obj = serializer.save()
        headers = self.get_success_headers(serializer.data)

        obj.from_addr.nonce += 1
        obj.from_addr.save()
        

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    # def validate(self, data):
    #     return data


class TransactionList(generics.ListAPIView):
    # TODO: different serializer??
    serializer_class = TransactionSerializer
    filterset_fields = ['from_addr__walletID', 'to_addr__walletID', 'amount']
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        # TODO: adjust transactions belonging to wallets of the signed in user
        return TokenTransaction.objects.all()

# wallet list by user
