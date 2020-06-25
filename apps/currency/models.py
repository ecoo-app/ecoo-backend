from django.db import models

from project.mixins import UUIDModel

class Currency(UUIDModel):
    name = models.CharField(max_length=32)

    # TODO: additional fields?
    def __str__(self):
        return self.name