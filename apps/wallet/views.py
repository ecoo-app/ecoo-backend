from django_filters.rest_framework import DjangoFilterBackend
from project.utils import raise_api_exception
import binascii

import pytezos
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from pytezos import Key
from rest_framework import generics, mixins, status, filters
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import BasePermission

from apps.wallet.models import WALLET_CATEGORIES, WALLET_STATES, CashOutRequest, Transaction, MetaTransaction, Wallet, WalletPublicKeyTransferRequest
from apps.wallet.serializers import CashOutRequestSerializer, MetaTransactionSerializer, TransactionSerializer, WalletSerializer, WalletPublicKeyTransferRequestSerializer
from apps.wallet.utils import create_message, read_nonce_from_chain


class WalletDetail(generics.RetrieveAPIView):
    lookup_field = "wallet_id"
    serializer_class = WalletSerializer

    def get_queryset(self):
        return Wallet.objects.all()


class WalletListCreate(generics.ListCreateAPIView):

    serializer_class = WalletSerializer
    filterset_fields = ['currency']

    def get_queryset(self):
        return self.request.user.wallets


class TransactionList(generics.ListAPIView):
    serializer_class = TransactionSerializer

    filterset_fields = ['from_wallet__wallet_id',
                        'to_wallet__wallet_id', 'amount']
    search_fields = ['=from_wallet__wallet_id', '=to_wallet__wallet_id']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    def get_queryset(self):
        return Transaction.objects.filter(Q(from_wallet__owner=self.request.user) | Q(to_wallet__owner=self.request.user))


class MetaTransactionListCreate(generics.ListCreateAPIView):
    serializer_class = MetaTransactionSerializer

    filterset_fields = ['from_wallet__wallet_id',
                        'to_wallet__wallet_id', 'amount']
    search_fields = ['=from_wallet__wallet_id', '=to_wallet__wallet_id']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    def get_queryset(self):
        return MetaTransaction.objects.filter(Q(from_wallet__owner=self.request.user) | Q(to_wallet__owner=self.request.user))


class WalletPublicKeyTransferRequestListCreate(generics.ListCreateAPIView):
    serializer_class = WalletPublicKeyTransferRequestSerializer

    def get_queryset(self):
        return WalletPublicKeyTransferRequest.objects.filter(wallet__owner=self.request.user)


class CashOutRequestListCreate(generics.ListCreateAPIView):
    serializer_class = CashOutRequestSerializer

    def get_queryset(self):
        return CashOutRequest.objects.filter(transaction__from_wallet__owner=self.request.user)
