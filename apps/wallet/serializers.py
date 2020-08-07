from rest_framework import serializers
import collections
from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import CashOutRequest, MetaTransaction, Transaction, Wallet, WalletPublicKeyTransferRequest


class WalletSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all())
    currency_details = CurrencySerializer(source='currency', read_only=True)

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = Wallet
        fields = ['owner', 'wallet_id', 'balance', 'public_key',
                  'nonce', 'currency', 'currency_details', 'category', 'state']
        read_only_fields = ['state', 'created_at']


class WalletPublicKeyTransferRequestSerializer(serializers.ModelSerializer):
    wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                          slug_field='wallet_id', queryset=Wallet.objects.all())

    def validate_wallet(self, value):
        if value.owner != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = WalletPublicKeyTransferRequest
        fields = ['wallet', 'old_public_key',
                  'new_public_key', 'state', 'submitted_to_chain_at', 'operation_hash']
        read_only_fields = ['state', 'created_at',
                            'submitted_to_chain_at', 'operation_hash']


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
                  'amount', 'state', 'tag', 'created_at', 'submitted_to_chain_at', 'operation_hash']
        read_only_fields = ['state', 'created_at',
                            'submitted_to_chain_at', 'operation_hash']


class MetaTransactionSerializer(TransactionSerializer):

    class Meta:
        model = MetaTransaction
        fields = ['from_wallet', 'to_wallet', 'amount',
                  'state', 'tag', 'created_at', 'signature', 'nonce']
        read_only_fields = ['state', 'created_at']


class CashOutRequestSerializer(serializers.ModelSerializer):
    transaction = serializers.PrimaryKeyRelatedField(
        queryset=Transaction.objects.all())

    def validate_transaction(self, value):
        if value.from_wallet.owner != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = CashOutRequest
        fields = ['transaction', 'beneficiary_name',
                  'beneficiary_iban', 'created_at', 'state']
        read_only_fields = ['state', 'created_at']
