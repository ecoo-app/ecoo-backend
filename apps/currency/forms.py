from django import forms

from apps.currency.models import Currency


class CsvImportForm(forms.Form):
    # currency = forms.
    csv_file = forms.ModelChoiceField(queryset=Currency.objects.all())


class PaperWalletCreateForm(forms.Form):
    _currency = forms.UUIDField(widget=forms.HiddenInput)
    _type_of_wallet = forms.IntegerField(widget=forms.HiddenInput)
    number_of_wallets = forms.IntegerField()
