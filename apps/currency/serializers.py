from rest_framework import serializers

from apps.currency.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['uuid', 'name', 'token_id']
