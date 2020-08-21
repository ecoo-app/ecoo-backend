from rest_framework import serializers
import collections
from apps.profiles.models import UserProfile, CompanyProfile
from apps.wallet.models import Wallet


class CompanyProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                          slug_field='wallet_id', queryset=Wallet.objects.all())

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = CompanyProfile
        fields = ['owner', 'uuid', 'name', 'uid', 'address_street',
                  'address_town', 'verification_stage', 'wallet', 'address_postal_code']


class UserProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    wallet = serializers.SlugRelatedField(many=False, read_only=False,
                                          slug_field='wallet_id', queryset=Wallet.objects.all())

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = UserProfile
        fields = ['owner', 'uuid', 'first_name', 'last_name', 'address_street',
                  'address_town', 'address_postal_code', 'telephone_number', 'verification_stage', 'wallet', 'date_of_birth']


class AutocompleteUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ['address_street', 'address_town', 'address_postal_code',]

class AutocompleteCompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyProfile
        fields = ['address_street', 'address_town', 'address_postal_code',]        