from rest_framework import serializers

from apps.verification.models import VerificationInput, VerificationInputData
from apps.currency.serializers import CurrencySerializer

class VerificationInputSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()
    input_type_display = serializers.CharField(source='get_input_type_display')

    class Meta:
        model = VerificationInput
        fields = ['uuid','name', 'input_type_display', 'used_for_companies','currency']


class VerificationInputDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationInputData
        fields = ['verification_input__uuid', 'data']
