
from django.db import models

from apps.municipality.models import Municipality

class MunicipalityOwnedMixin(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True,)

    class Meta:
        abstract = True
