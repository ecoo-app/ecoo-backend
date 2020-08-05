from rest_framework import serializers
import collections
from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import MetaTransaction, Transaction, Wallet, WalletPublicKeyTransferRequest


class WalletSerializer(serializers.ModelSerializer):
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all())

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = Wallet
        fields = ['wallet_id', 'balance', 'public_key',
                  'nonce', 'currency', 'category', 'state']


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


class TransactionSerializer(serializers.ModelSerializer):
    from_wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                               slug_field='wallet_id', queryset=Wallet.objects.all())
    to_wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                             slug_field='wallet_id', queryset=Wallet.objects.all())

    def validate_from_wallet(self, value):
        if value.owner != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = Transaction
        fields = ['from_wallet', 'to_wallet',
                  'amount', 'state', 'tag', 'created_at']


class MetaTransactionSerializer(TransactionSerializer):

    class Meta:
        model = MetaTransaction
        fields = ['from_wallet', 'to_wallet', 'amount',
                  'state', 'tag', 'created_at', 'signature', 'nonce']
