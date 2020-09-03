from rest_framework import serializers
import collections
from apps.profiles.models import UserProfile, CompanyProfile
from apps.wallet.models import Wallet
from datetime import date

class CompanyProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                          slug_field='wallet_id', queryset=Wallet.objects.all())

    def validate_wallet(self, value):
        if value.currency.claim_deadline is not None and value.currency.claim_deadline < date.today():
            raise serializers.ValidationError("Currency deadline in the past")
        return value

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = CompanyProfile
        fields = ['owner', 'uuid', 'name', 'uid', 'address_street',
                  'address_town', 'verification_stage', 'wallet', 'address_postal_code']
        extra_kwargs = {'address_town': {'required': True}, 'address_street': {'required': True}, 'address_postal_code': {'required': True}} 



class UserProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                          slug_field='wallet_id', queryset=Wallet.objects.all())

    def validate_wallet(self, value):
        if value.currency.claim_deadline is not None and value.currency.claim_deadline < date.today():
            raise serializers.ValidationError("Currency deadline in the past")
        return value

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = UserProfile
        fields = ['owner', 'uuid', 'first_name', 'last_name', 'address_street',
                  'address_town', 'address_postal_code', 'telephone_number', 'verification_stage', 'wallet', 'date_of_birth']
