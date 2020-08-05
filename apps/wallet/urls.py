
from django.urls import include, path
from rest_framework import routers

from apps.wallet.views import (TransactionCreate, TransactionList,
                               WalletCreate, WalletPublicKeyTransferRequestListCreate, WalletDetail, WalletList,
                               get_nonce)

urlpatterns = [
    path('wallet/list/', WalletList.as_view(), name='wallet_list'),
    path('wallet/create/', WalletCreate.as_view(), name='wallet_create'),
    path('wallet/<slug:wallet_id>/', WalletDetail.as_view(), name='wallet_detail'),
    path('wallet/nonce/<slug:wallet_id>/', get_nonce, name='wallet_nonce'),

    path('wallet_public_key_transfer_request/',
         WalletPublicKeyTransferRequestListCreate.as_view(), name='wallet_public_key_transfer_request_list_create'),

    path('transaction/create/', TransactionCreate.as_view(), name='add_tx'),
    path('transaction/list/', TransactionList.as_view(), name='txs'),
]
