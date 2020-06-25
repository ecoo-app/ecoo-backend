from rest_framework import serializers
from apps.wallet.models import Wallet, TokenTransaction


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField('get_balance')

    def get_balance(self, wallet):
        # TODO: how to get balance of account?
        return 100.4

    class Meta:
        model = Wallet
        fields = ['walletID', 'balance', 'address', 'pub_key']


class PublicWalletSerializer(WalletSerializer):

    class Meta:
        model = Wallet
        fields = ['walletID', 'address', 'pub_key']


class TransactionSerializer(serializers.ModelSerializer):
    from_addr = serializers.SlugRelatedField(many=False, read_only=False,
                                             slug_field='walletID', queryset=Wallet.objects.all())
    to_addr = serializers.SlugRelatedField(many=False, read_only=False,
                                           slug_field='walletID', queryset=Wallet.objects.all())

    class Meta:
        model = TokenTransaction
        fields = ['from_addr', 'to_addr', 'amount', 'signature']

    # increase from wallet nonce