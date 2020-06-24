from django.contrib import admin
from apps.wallet.models import Wallet, TokenTransaction
# Register your models here.


admin.site.register(Wallet)
admin.site.register(TokenTransaction)