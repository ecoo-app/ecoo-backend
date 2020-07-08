from rest_framework import serializers


from apps.currency.models import Currency, VerificationInput

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['uuid','name']

class VerificationInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationInput
        fields = ['label', 'data_type']