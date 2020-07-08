import pytezos
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from pytezos import Key
from rest_framework import generics, mixins, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from apps.wallet.models import TokenTransaction, WALLET_STATES, Wallet
from apps.wallet.serializers import (CreateWalletSerializer,
                                     PublicWalletSerializer,
                                     TransactionSerializer, WalletSerializer)
from apps.wallet.utils import CustomCursorPagination


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
            serializer = WalletSerializer(wallet)
        else:
            serializer = PublicWalletSerializer(wallet)

        return Response(serializer.data)

@api_view(['GET'])
def get_nonce(request, walletID=None):

    if walletID:
        wallet = Wallet.objects.get(walletID=walletID)
        return Response({"nonce":str(wallet.nonce)})
    else:
        e = APIException()
        e.status_code = 422
        e.detail = 'walletID is invalid'
        raise e

class WalletCreate(generics.CreateAPIView):
    serializer_class = CreateWalletSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save()
        if obj.company:
            obj.owner = request.user
        else:
            if obj.company.owner != request.user:
                e = APIException()
                e.status_code = 403
                e.detail = "You aren't the owner of the company"
                raise e
        
        # TODO: create walletID

        obj.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED, headers=headers)


class WalletList(generics.ListAPIView):
    serializer_class = WalletSerializer
    filterset_fields = ['currency']

    def get_queryset(self):
        return Wallet.getBelongingToUser(self.request.user)


class TransactionCreate(generics.CreateAPIView):
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if self.request.user != serializer.validated_data['from_addr'].owner:
            raise PermissionDenied()

        from_address = serializer.validated_data['from_addr']
        to_address = serializer.validated_data['to_addr']

        if from_address.state != WALLET_STATES.VERIFIED:
            e = APIException()
            e.status_code = 403
            e.detail = 'Only verified addresses can send money'
            raise e


        key = Key.from_encoded_key(from_address.pub_key)
        data = {
            "prim": "pair",
            "args": [
                {"string": from_address.address},
                {
                    "prim": "pair",
                    "args": [
                            {"string": to_address.address},
                            {
                                "prim": "pair",
                                "args": [
                                        {"nat": serializer.validated_data['amount']},
                                        {"nat": serializer.validated_data['nonce']} # TODO: is this correct??
                                ]
                            }
                    ]
                }
            ]
        }

        forged_data = pytezos.michelson.forge.forge_micheline(data)

        if key.verify(self.request.data.get('signature'), forged_data) != None:
            e = APIException()
            e.status_code = 422
            e.detail = 'Signature is invalid'
            raise e

        if self.request.data.get('nonce') - serializer.validated_data['from_addr'].nonce != 1:
            e = APIException()
            e.status_code = 422
            e.detail = 'Nonce value is incorrect'
            raise e

        obj = serializer.save()
        headers = self.get_success_headers(serializer.data)

        obj.from_addr.nonce += 1
        obj.from_addr.save()

        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED, headers=headers)


class TransactionList(generics.ListAPIView):
    # TODO: different serializer??
    serializer_class = TransactionSerializer
    filterset_fields = ['from_addr__walletID', 'to_addr__walletID', 'amount']
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        if self.request.user.is_superuser:
            return TokenTransaction.objects.all()
        return TokenTransaction.getBelongingToUser(self.request.user)

# TODO: verify_wallet 
