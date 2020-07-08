from django.contrib import admin
from apps.wallet.models import ClaimableAmount, Company, TokenTransaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    fields = ('currency', 'walletID', 'owner', 'pub_key',)
    list_display = ('walletID', 'owner', 'pub_key')


@admin.register(TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    list_display = ['from_addr', 'to_addr', 'amount', 'state']


# TODO: add proper admin sites
admin.site.register(Company)
admin.site.register(ClaimableAmount)
