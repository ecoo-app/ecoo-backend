import secrets
import string
from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Q, Sum
from django.db.models.signals import pre_save
from django.utils.crypto import get_random_string

from project.mixins import UUIDModel
from django.utils.translation import ugettext_lazy as _


class CompanyProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.DO_NOTHING, related_name='company_profiles')

    name = models.CharField(max_length=128)
    uid = models.CharField(max_length=15, blank=True)

    address_street = models.CharField(max_length=128, blank=True)
    address_town = models.CharField(max_length=128, blank=True)
    address_postal_code = models.CharField(max_length=128, blank=True)

    @property
    def verification_stage(self):
        if hasattr(self, 'company_verification'):
            if self.address_pin_verification.state == 3:
                return 2
            else:
                return 1
        else:
            return 0

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = _('Company Profiles')


class UserProfile(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.DO_NOTHING, related_name='user_profiles')

    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)

    address_street = models.CharField(max_length=128, blank=True)
    address_town = models.CharField(max_length=128, blank=True)
    address_postal_code = models.CharField(max_length=128, blank=True)

    telephone_number = models.CharField(max_length=16)
    date_of_birth = models.DateField()

    @property
    def verification_stage(self):
        if hasattr(self, 'user_verification'):
            if self.sms_pin_verification.state == 3:
                return 2
            else:
                return 1
        else:
            return 0

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = _('User Profiles')
