from django.contrib import admin
from apps.wallet.models import ClaimableAmount, Company, Transaction, MetaTransaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    fields = ('currency', 'wallet_id', 'owner', 'public_key', 'state')
    list_display = ('wallet_id', 'owner', 'state')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['from_wallet', 'to_wallet', 'amount', 'state']


@admin.register(MetaTransaction)
class MetaTransactionAdmin(admin.ModelAdmin):
    list_display = ['from_wallet', 'to_wallet', 'amount', 'state']


# TODO: add proper admin sites
admin.site.register(Company)
admin.site.register(ClaimableAmount)
