from rest_framework import serializers

from apps.wallet.models import TokenTransaction, Wallet
from apps.currency.serializers import CurrencySerializer
from apps.currency.models import Currency


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField('get_balance')
    actual_nonce = serializers.SerializerMethodField('get_nonce')
    currency = CurrencySerializer()

    def get_balance(self, wallet):
        # TODO: get balance of account on blockchain & apply the transactions stored but not commited
        # entry point get_balance -> move function to utils
        return 100.4

    def get_nonce(self, wallet):
        return wallet.nonce

    class Meta:
        model = Wallet
        fields = ['walletID', 'balance', 'address',
                  'pub_key', 'actual_nonce', 'currency']


class CreateWalletSerializer(serializers.ModelSerializer):
    verification_uuid = serializers.UUIDField(required=False)
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all())

    class Meta:
        model = Wallet
        fields = ['address', 'pub_key', 'company', 'currency', 'verification_uuid']


class PublicWalletSerializer(WalletSerializer):

    class Meta:
        model = Wallet
        fields = ['walletID', 'address', 'pub_key', 'currency']


class TransactionSerializer(serializers.ModelSerializer):
    from_addr = serializers.SlugRelatedField(many=False, read_only=False,
                                             slug_field='walletID', queryset=Wallet.objects.all())
    to_addr = serializers.SlugRelatedField(many=False, read_only=False,
                                           slug_field='walletID', queryset=Wallet.objects.all())

    class Meta:
        model = TokenTransaction
        fields = ['from_addr', 'to_addr', 'amount', 'signature']

    # increase from wallet nonce
