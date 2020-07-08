
from django.urls import include, path
from rest_framework import routers

from apps.wallet.views import (TransactionCreate, TransactionList,
                               WalletDetail, WalletList, WalletCreate)

urlpatterns = [
    path('wallet/list/', WalletList.as_view(), name='wallet_list'),
    path('wallet/create/', WalletCreate.as_view(), name='wallet_create'),
    path('wallet/<slug:walletID>/', WalletDetail.as_view(), name='wallet_detail'),

    path('transaction/', TransactionCreate.as_view(), name='add_tx'),
    path('transaction/list/', TransactionList.as_view(), name='txs'),

]
