from rest_framework import serializers
import collections
from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import MetaTransaction, Transaction, Wallet, WalletPublicKeyTransferRequest


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


class WalletPublicKeyTransferRequestSerializer(serializers.ModelSerializer):
    wallet = serializers.PrimaryKeyRelatedField(queryset=Wallet.objects.all())

    def validate_wallet(self, value):
        if value.owner != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = WalletPublicKeyTransferRequest
        fields = ['wallet', 'old_public_key',
                  'new_public_key', 'state', 'submitted_to_chain_at', 'operation_hash']


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
    signature = serializers.SerializerMethodField()

    def get_signature(self, obj):
        if not type(obj) is collections.OrderedDict and MetaTransaction.objects.filter(uuid=obj.uuid).exists():
            return MetaTransaction.objects.get(uuid=obj.uuid).signature
        return ''

    class Meta:
        model = Transaction
        fields = ['from_wallet', 'to_wallet',
                  'signature', 'amount', 'state', 'tag']
