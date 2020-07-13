from rest_framework import serializers

from apps.wallet.models import TokenTransaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField('get_balance')
    actual_nonce = serializers.SerializerMethodField('get_nonce')

    def get_balance(self, wallet):
        # TODO: get balance of account on blockchain & apply the transactions stored but not commited
        # entry point get_balance -> move function to utils
        return 100.4

    def get_nonce(self, wallet):
        return wallet.nonce

    class Meta:
        model = Wallet
        fields = ['walletID', 'balance', 'address', 'pub_key', 'actual_nonce']


class CreateWalletSerializer(serializers.ModelSerializer):
    verification_uuid = serializers.UUIDField(required=False)

    class Meta:
        model = Wallet
        fields = ['address', 'pub_key', 'company']


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
