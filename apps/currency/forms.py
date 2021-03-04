from django import forms
from apps.currency.models import Currency


class CsvImportForm(forms.Form):
    # currency = forms.
    csv_file = forms.ModelChoiceField(queryset=Currency.objects.all())
