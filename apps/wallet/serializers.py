from rest_framework import serializers

from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import TokenTransaction, Wallet
from apps.wallet.utils import getBalanceForWallet


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField('get_balance')
    actual_nonce = serializers.SerializerMethodField('get_nonce')
    currency = CurrencySerializer()

    def get_balance(self, wallet):
        return getBalanceForWallet(wallet)

    def get_nonce(self, wallet):
        return wallet.nonce

    class Meta:
        model = Wallet
        fields = ['walletID', 'balance', 'pub_key',
                  'actual_nonce', 'currency', 'category']


class CreateWalletSerializer(serializers.ModelSerializer):
    verification_uuid = serializers.UUIDField(required=False)
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all())

    class Meta:
        model = Wallet
        fields = ['pub_key', 'company',
                  'currency', 'verification_uuid', 'category']


class PublicWalletSerializer(WalletSerializer):

    class Meta:
        model = Wallet
        fields = ['walletID', 'pub_key', 'currency', 'category']


class TransactionSerializer(serializers.ModelSerializer):
    from_addr = serializers.SlugRelatedField(many=False, read_only=False,
                                             slug_field='walletID', queryset=Wallet.objects.all())
    to_addr = serializers.SlugRelatedField(many=False, read_only=False,
                                           slug_field='walletID', queryset=Wallet.objects.all())

    class Meta:
        model = TokenTransaction
        fields = ['from_addr', 'to_addr', 'amount', 'signature']
