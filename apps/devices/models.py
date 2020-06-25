from django.db import models
from project.mixins import UUIDModel

class Device(UUIDModel):
    token = models.CharField(max_length=128)
    pass