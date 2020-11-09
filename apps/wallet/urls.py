
from django.urls import path

from apps.wallet.views import (CashOutRequestListCreate,
                               MetaTransactionListCreate, OpenCashoutTransactions, TransactionList,
                               WalletDetail, WalletListCreate,
                               WalletPublicKeyTransferRequestListCreate)

urlpatterns = [
    path('wallet/', WalletListCreate.as_view(), name='wallet_list_create'),
    path('wallet/<slug:wallet_id>/', WalletDetail.as_view(), name='wallet_detail'),
    path('wallet_public_key_transfer_request/',
         WalletPublicKeyTransferRequestListCreate.as_view(), name='wallet_public_key_transfer_request_list_create'),
    path('cash_out_request/',
         CashOutRequestListCreate.as_view(), name='cash_out_request_list_create'),

    path('transaction/', TransactionList.as_view(),
         name='transaction_list'),
    path('open_cashout_transaction/', OpenCashoutTransactions.as_view(),
         name='open_cashout_list'),
    path('meta_transaction/', MetaTransactionListCreate.as_view(),
         name='meta_transaction_list_create'),
]
