import collections

from rest_framework import serializers

from apps.currency.models import Currency
from apps.currency.serializers import CurrencySerializer
from apps.wallet.models import (
    WALLET_CATEGORIES,
    CashOutRequest,
    MetaTransaction,
    PaperWallet,
    Transaction,
    Wallet,
    WalletPublicKeyTransferRequest,
)


class PublicWalletSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all())
    currency_details = CurrencySerializer(source="currency", read_only=True)

    class Meta:
        model = Wallet
        fields = [
            "owner",
            "wallet_id",
            "public_key",
            "nonce",
            "currency",
            "currency_details",
            "category",
            "state",
        ]
        read_only_fields = [
            "state",
        ]


class PublicPaperWalletSerializer(PublicWalletSerializer):
    class Meta(PublicWalletSerializer.Meta):
        model = PaperWallet
        fields = PublicWalletSerializer.Meta.fields + ["can_be_used_for_verification"]


class WalletSerializer(PublicWalletSerializer):
    def validate_owner(self, value):
        if value != self.context["request"].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    def validate_category(self, value):
        if value not in [
            WALLET_CATEGORIES.COMPANY.value,
            WALLET_CATEGORIES.CONSUMER.value,
        ]:
            raise serializers.ValidationError(
                "Only wallet category CONSUMER and COMPANY is allowed"
            )
        return value

    class Meta:
        model = Wallet
        fields = [
            "owner",
            "wallet_id",
            "balance",
            "public_key",
            "nonce",
            "currency",
            "currency_details",
            "category",
            "state",
        ]
        read_only_fields = ["state", "created_at"]


class PaperWalletSerializer(
    WalletSerializer,
):
    class Meta(WalletSerializer.Meta):
        model = PaperWallet
        fields = WalletSerializer.Meta.fields + ["can_be_used_for_verification"]


class WalletPublicKeyTransferRequestSerializer(serializers.ModelSerializer):
    wallet = serializers.SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="wallet_id",
        queryset=Wallet.objects.all(),
    )

    def validate_wallet(self, value):
        if value.owner != self.context["request"].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = WalletPublicKeyTransferRequest
        fields = [
            "wallet",
            "old_public_key",
            "new_public_key",
            "state",
            "submitted_to_chain_at",
            "operation_hash",
        ]
        read_only_fields = [
            "state",
            "created_at",
            "submitted_to_chain_at",
            "operation_hash",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    from_wallet = serializers.SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="wallet_id",
        queryset=Wallet.objects.all(),
    )
    to_wallet = serializers.SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="wallet_id",
        queryset=Wallet.objects.all(),
    )
    notes = serializers.CharField(source="user_notes", allow_blank=True, required=False)

    # def validate_from_wallet(self, value):
    #     if value.owner != self.context['request'].user:
    #         raise serializers.ValidationError("Does not belong to user")
    #     return value

    class Meta:
        model = Transaction
        fields = [
            "uuid",
            "from_wallet",
            "to_wallet",
            "amount",
            "state",
            "tag",
            "created_at",
            "submitted_to_chain_at",
            "operation_hash",
            "notes",
        ]
        read_only_fields = [
            "state",
            "created_at",
            "submitted_to_chain_at",
            "operation_hash",
        ]


class MetaTransactionSerializer(TransactionSerializer):
    notes = serializers.CharField(source="user_notes", allow_blank=True, required=False)

    class Meta:
        model = MetaTransaction
        fields = [
            "uuid",
            "from_wallet",
            "to_wallet",
            "amount",
            "state",
            "tag",
            "created_at",
            "signature",
            "nonce",
            "notes",
        ]
        read_only_fields = ["state", "created_at"]

    # FIXME: add validation if its a 'activation'-transaction and check for sms verfication if needed (currency)


class CashOutRequestSerializer(serializers.ModelSerializer):
    transaction = serializers.PrimaryKeyRelatedField(queryset=Transaction.objects.all())

    def validate_transaction(self, value):
        if value.from_wallet.owner != self.context["request"].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = CashOutRequest
        fields = [
            "transaction",
            "beneficiary_name",
            "beneficiary_iban",
            "created_at",
            "state",
        ]
        read_only_fields = ["state", "created_at"]
