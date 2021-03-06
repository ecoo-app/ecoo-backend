from django import forms
from django.utils.translation import ugettext_lazy as _

from apps.currency.models import Currency
from apps.wallet.models import Transaction, Wallet


class GenerateWalletForm(forms.Form):
    amount = forms.IntegerField(label=_("Amount"))
    currency = forms.ModelChoiceField(
        label=_("Currency"), queryset=Currency.objects.all()
    )


class TransactionAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["from_wallet"].choices = [(None, "No Wallet")] + list(
            Wallet.objects.values_list("pk", "wallet_id")
        )
        self.fields["to_wallet"].choices = Wallet.objects.values_list("pk", "wallet_id")

    class Meta:
        model = Transaction
        fields = "__all__"
