from django.db import models
from django.utils import timezone
import uuid


class UUIDModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(null=True, auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True
