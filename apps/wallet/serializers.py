from rest_framework import serializers

from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import MetaTransaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    actual_nonce = serializers.SerializerMethodField('get_nonce')
    currency = CurrencySerializer()
    state = serializers.CharField(source='get_state_display')
    category = serializers.CharField(source='get_category_display') 
    
    def get_nonce(self, wallet):
        return wallet.nonce

    class Meta:
        model = Wallet
        fields = ['wallet_id', 'balance', 'public_key',
                  'actual_nonce', 'currency', 'category', 'state']


class CreateWalletSerializer(serializers.ModelSerializer):
    verification_uuid = serializers.UUIDField(required=False)
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all())

    class Meta:
        model = Wallet
        fields = ['public_key', 'company',
                  'currency', 'verification_uuid', 'category']


class PublicWalletSerializer(WalletSerializer):

    class Meta:
        model = Wallet
        fields = ['wallet_id', 'public_key', 'currency', 'category', 'state']


class TransactionSerializer(serializers.ModelSerializer):
    from_wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                               slug_field='wallet_id', queryset=Wallet.objects.all())
    to_wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                             slug_field='wallet_id', queryset=Wallet.objects.all())
    state = serializers.CharField(source='get_state_display', read_only=True)
    class Meta:
        model = MetaTransaction
        fields = ['from_wallet', 'to_wallet', 'amount', 'signature', 'state']
