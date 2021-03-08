import pytezos
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, serializers

from apps.wallet.utils import create_paper_wallet_message
from apps.wallet.models import (WALLET_STATES, CashOutRequest, MetaTransaction,
                                Transaction, Wallet,
                                WalletPublicKeyTransferRequest, PaperWallet)
from apps.wallet.serializers import (CashOutRequestSerializer,
                                     MetaTransactionSerializer,
                                     PublicWalletSerializer,
                                     TransactionSerializer,
                                     WalletPublicKeyTransferRequestSerializer,
                                     WalletSerializer)


class WalletDetail(generics.RetrieveAPIView):
    lookup_field = "wallet_id"
    serializer_class = WalletSerializer

    def get_queryset(self):
        return Wallet.objects.all()

    def get_serializer_class(self):
        wallet = self.get_object()

        if wallet.owner == self.request.user:
            return WalletSerializer
        else:
            return PublicWalletSerializer


class PaperWalletDetail(WalletDetail):

    def get_serializer_class(self):
        wallet = self.get_object()
        message_verified = False
        if self.kwargs.get('signature',None):
            try:
                key = pytezos.Key.from_encoded_key(wallet.public_key)
                key.verify(self.kwargs['signature'], create_paper_wallet_message(wallet, wallet.currency.token_id))
                message_verified = True
            except ValueError:
                raise serializers.ValidationError('invalid signature')
                # branch out from dev
        if wallet.owner == self.request.user or message_verified:
            return WalletSerializer
        else:
            return PublicWalletSerializer


class WalletListCreate(generics.ListCreateAPIView):
    serializer_class = WalletSerializer
    filterset_fields = ['currency']

    def get_queryset(self):
        return self.request.user.wallets.exclude(state=WALLET_STATES.DEACTIVATED.value)


class TransactionList(generics.ListAPIView):
    serializer_class = TransactionSerializer

    filterset_fields = ['from_wallet__wallet_id',
                        'to_wallet__wallet_id', 'amount']
    search_fields = ['=from_wallet__wallet_id', '=to_wallet__wallet_id']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    def get_queryset(self):
        return Transaction.objects.filter(Q(from_wallet__owner=self.request.user) | Q(to_wallet__owner=self.request.user)).order_by('-created_at')


class OpenCashoutTransactions(TransactionList):
    def get_queryset(self):
        cashout_ids = [str(tx.uuid) for tx in Transaction.objects.filter(from_wallet__owner=self.request.user) if tx.is_cashout_transaction]
        return Transaction.objects.filter(uuid__in=cashout_ids, cash_out_requests__isnull=True).order_by('-created_at')


class MetaTransactionListCreate(generics.ListCreateAPIView):
    serializer_class = MetaTransactionSerializer

    filterset_fields = ['from_wallet__wallet_id',
                        'to_wallet__wallet_id', 'amount']
    search_fields = ['=from_wallet__wallet_id', '=to_wallet__wallet_id']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    def get_queryset(self):
        return MetaTransaction.objects.filter(Q(from_wallet__owner=self.request.user) | Q(to_wallet__owner=self.request.user)).order_by('-created_at')


class WalletPublicKeyTransferRequestListCreate(generics.ListCreateAPIView):
    serializer_class = WalletPublicKeyTransferRequestSerializer

    def get_queryset(self):
        return WalletPublicKeyTransferRequest.objects.filter(wallet__owner=self.request.user)


class CashOutRequestListCreate(generics.ListCreateAPIView):
    serializer_class = CashOutRequestSerializer

    def get_queryset(self):
        return CashOutRequest.objects.filter(transaction__from_wallet__owner=self.request.user)
