from rest_framework import serializers
import collections
from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import MetaTransaction, Transaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    actual_nonce = serializers.SerializerMethodField('get_nonce')
    currency = CurrencySerializer()

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
    signature = serializers.SerializerMethodField()

    def get_signature(self, obj):
        if not type(obj) is collections.OrderedDict and MetaTransaction.objects.filter(uuid=obj.uuid).exists():
            return MetaTransaction.objects.get(uuid=obj.uuid).signature
        return ''

    class Meta:
        model = Transaction
        fields = ['from_wallet', 'to_wallet',
                  'signature', 'amount', 'state', 'tag', 'created_at']
