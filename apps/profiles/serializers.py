from rest_framework import serializers
import collections
from apps.profiles.models import UserProfile, CompanyProfile


class CompanyProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = CompanyProfile
        fields = ['owner', 'uuid', 'name', 'uid', 'address_street',
                  'address_town', 'verification_stage', 'address_postal_code']


class UserProfileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    def validate_owner(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError("Does not belong to user")
        return value

    class Meta:
        model = UserProfile
        fields = ['owner', 'uuid', 'first_name', 'last_name', 'address_street',
                  'address_town', 'address_postal_code', 'telephone_number', 'verification_stage', 'date_of_birth']
