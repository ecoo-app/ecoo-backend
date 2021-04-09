from django import forms
from django.forms import FileInput
from django.utils.translation import ugettext_lazy as _

from apps.currency.models import Currency


class ImportForm(forms.Form):
    csv_file = forms.FileField(label=_("CSV file"), widget=FileInput)

    def __init__(self, *args, **kwargs):
        super(ImportForm, self).__init__(*args, **kwargs)
        self.fields["csv_file"].widget.attrs["accept"] = "text/csv"
