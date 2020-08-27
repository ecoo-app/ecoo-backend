from rest_framework import serializers

from apps.verification.models import CompanyVerification, UserVerification


class AutocompleteUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserVerification
        fields = ['address_street',]


class AutocompleteCompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyVerification
        fields = ['address_street',]
