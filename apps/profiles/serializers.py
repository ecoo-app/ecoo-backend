import collections
from datetime import date

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from apps.profiles.models import CompanyProfile, UserProfile
from apps.wallet.models import Wallet


class CompanyProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    wallet = serializers.SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="wallet_id",
        queryset=Wallet.objects.all(),
    )

    def validate_wallet(self, value):
        if (
            value.currency.claim_deadline is not None
            and value.currency.claim_deadline < date.today()
        ):
            raise serializers.ValidationError(_("Currency deadline in the past"))
        return value

    def validate_owner(self, value):
        if value != self.context["request"].user:
            raise serializers.ValidationError(_("Does not belong to user"))
        return value

    class Meta:
        model = CompanyProfile
        fields = [
            "owner",
            "uuid",
            "name",
            "uid",
            "address_street",
            "address_town",
            "verification_stage",
            "wallet",
            "address_postal_code",
            "phone_number",
        ]
        extra_kwargs = {
            "address_town": {"required": True},
            "address_street": {"required": True},
            "address_postal_code": {"required": True},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    wallet = serializers.SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="wallet_id",
        queryset=Wallet.objects.all(),
    )

    def validate_wallet(self, value):
        if (
            value.currency.claim_deadline is not None
            and value.currency.claim_deadline < date.today()
        ):
            raise serializers.ValidationError(_("Currency deadline in the past"))
        return value

    def validate_owner(self, value):
        if value != self.context["request"].user:
            raise serializers.ValidationError(_("Does not belong to user"))
        return value

    def validate_place_of_origin(self, value):
        return value.strip()

    class Meta:
        model = UserProfile
        fields = [
            "owner",
            "uuid",
            "first_name",
            "last_name",
            "address_street",
            "address_town",
            "address_postal_code",
            "telephone_number",
            "verification_stage",
            "wallet",
            "date_of_birth",
            "place_of_origin",
        ]
