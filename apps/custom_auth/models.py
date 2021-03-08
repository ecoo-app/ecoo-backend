from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    # we can't set uuid because of jet
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # TODO: adjust once it's clear
    # ahv_number = models.Textfield()
    # dob = models.Datefield()
    # municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True,)

    pass
