import binascii

import pytezos
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from pytezos import Key
from rest_framework import generics, mixins, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.wallet.models import (WALLET_CATEGORIES, WALLET_STATES,
                                Transaction, MetaTransaction, Wallet)
from apps.wallet.serializers import (CreateWalletSerializer,
                                     PublicWalletSerializer,
                                     TransactionSerializer, WalletSerializer)
from apps.wallet.utils import (CustomCursorPagination, create_message,
                               read_nonce_from_chain)
from project.utils import raise_api_exception


class WalletDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    lookup_field = "wallet_id"
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    public_serializer = PublicWalletSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        wallet = self.get_object()

        if request and (request.user.is_superuser == True or request.user == wallet.owner):
            serializer = WalletSerializer(wallet)
        else:
            serializer = PublicWalletSerializer(wallet)

        return Response(serializer.data)


@api_view(['GET'])
def get_nonce(request, wallet_id=None):

    if wallet_id:
        wallet = Wallet.objects.get(wallet_id=wallet_id)
        return Response({"nonce": str(wallet.nonce)})
    else:
        raise_api_exception(422, 'wallet_id is invalid')


class WalletCreate(generics.CreateAPIView):
    serializer_class = CreateWalletSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        obj = Wallet(**serializer.validated_data)

        if not obj.company:
            obj.owner = request.user
        else:
            if validated_data['company'].owner != request.user:
                raise_api_exception(403, "You aren't the owner of the company")

        retry = True
        while retry:
            try:
                retry = False
                obj.wallet_id = Wallet.generate_wallet_id()
                obj.save()
            except IntegrityError:
                retry = True

        if validated_data.get('verification_uuid', None):
            # TODO: handle verification
            pass
            # verification_data = VerificationData.objects.get(
            #     uuid=validated_data['verification_uuid'])
            # if verification_data.has_been_used or (obj.owner and obj.owner != verification_data['owner']) or (obj.company and obj.company != verification_data['company']):
            #     pass
            # else:
            #     obj.state = WALLET_STATES.VERIFIED.value
            #     verification_data.has_been_used = True
            #     verification_data.save()

        if request.data.get('is_company_wallet', False):
            obj.category = WALLET_CATEGORIES.COMPANY.value

        obj.save()

        headers = self.get_success_headers(serializer.data)
        return Response(WalletSerializer(obj).data, status=status.HTTP_201_CREATED, headers=headers)
        # return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED, headers=headers)


class WalletList(generics.ListAPIView):
    serializer_class = WalletSerializer
    filterset_fields = ['currency']

    def get_queryset(self):
        return self.request.user.wallets


class TransactionCreate(generics.CreateAPIView):
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user != serializer.validated_data['from_wallet'].owner:
            raise PermissionDenied()

        from_wallet = serializer.validated_data['from_wallet']
        to_wallet = serializer.validated_data['to_wallet']

        if from_wallet.state != WALLET_STATES.VERIFIED.value:
            raise_api_exception(403, 'Only verified addresses can send money')

        if from_wallet.currency != to_wallet.currency:
            raise_api_exception(
                422, 'Both wallets have to belong to the same currency')

        if not self.request.data.get('nonce', None) or int(self.request.data.get('nonce')) - serializer.validated_data['from_wallet'].nonce != 1:
            raise_api_exception(422, 'Nonce value is incorrect')

        if from_wallet.balance < serializer.validated_data['amount']:
            raise_api_exception(422, 'Balance is too small')

        signature = self.request.data.get('signature')

        token_id = from_wallet.currency.token_id
        message = create_message(
            from_wallet, to_wallet, request.data['nonce'], token_id, serializer.validated_data['amount'])
        key = pytezos.Key.from_encoded_key(from_wallet.public_key)

        try:
            res = key.verify(signature, message)
        except ValueError:
            raise_api_exception(422, 'Signature is invalid')

        key_2 = Key.from_encoded_key(settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY)
        last_nonce = read_nonce_from_chain(
            key_2.public_key_hash())
        obj = MetaTransaction(**serializer.validated_data)
        obj.nonce = last_nonce
        obj.save()

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TransactionList(generics.ListAPIView):
    # TODO: different serializer??
    serializer_class = TransactionSerializer
    filterset_fields = ['from_wallet__wallet_id',
                        'to_wallet__wallet_id', 'amount']
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Transaction.objects.all()

        wallet_of_interest = self.request.query_params.get('wallet_id', None)
        if wallet_of_interest:
            return Transaction.get_belonging_to_user(self.request.user).filter(Q(from_wallet__wallet_id=wallet_of_interest) | Q(to_wallet__wallet_id=wallet_of_interest))

        return Transaction.get_belonging_to_user(self.request.user)


@api_view(['POST'])
def migrate_wallet(request):
    # TODO: implement

    return JsonResponse({'foo': 'bar'})
    # return Response({'msg':'ok'}, status=status.HTTP_201_CREATED)
