from rest_framework import serializers

from apps.verification.models import CompanyVerification, UserVerification


class AutocompleteUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserVerification
        fields = ['address_street', 'address_town', 'address_postal_code']


class AutocompleteCompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyVerification
        fields = ['address_street', 'address_town', 'address_postal_code']
