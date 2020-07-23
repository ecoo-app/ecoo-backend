from django.contrib import admin
from apps.wallet.models import Company, Transaction, MetaTransaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    fields = ['currency', 'wallet_id', 'category', 'owner', 'public_key', 'state']
    list_display = ['wallet_id', 'owner', 'state']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['from_wallet', 'to_wallet', 'amount', 'state']
    list_filter = ['from_wallet__currency', 'state']
    search_fields = ['from_wallet__wallet_id', 'to_wallet__wallet_id']


@admin.register(MetaTransaction)
class MetaTransactionAdmin(admin.ModelAdmin):
    list_display = ['from_wallet', 'to_wallet', 'amount', 'state']
    list_filter = ['from_wallet__currency', 'state']
    search_fields = ['from_wallet__wallet_id', 'to_wallet__wallet_id']


# TODO: add proper admin sites
admin.site.register(Company)
