
from django.urls import include, path
from rest_framework import routers

from apps.wallet.views import (TransactionDetail, TransactionList,
                               WalletDetail, WalletList)

urlpatterns = [
    path('wallet/<slug:walletID>/', WalletDetail.as_view(), name='wallet_detail'),
    path('wallets/', WalletList.as_view(), name='wallet_list'),
    path('transaction/', TransactionDetail.as_view(), name='add_tx'),
    path('transactions/', TransactionList.as_view(), name='txs')
]
