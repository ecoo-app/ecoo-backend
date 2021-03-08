from django import forms
from django.forms import FileInput
from django.utils.translation import ugettext_lazy as _

from apps.currency.models import Currency


class GenerateWalletForm(forms.Form):
    amount = forms.IntegerField(label=_("Amount"))
    currency = forms.ModelChoiceField(
        label=_("Currency"), queryset=Currency.objects.all()
    )
