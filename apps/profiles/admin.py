from django.contrib import admin, messages
from apps.profiles.models import UserProfile, CompanyProfile
from django.utils.translation import ugettext_lazy as _
import requests
from django.conf import settings
from django import forms
import datetime
from django.shortcuts import render
from apps.profiles.filters import VerificationLevelFilter


@admin.register(UserProfile)
class UserProfile(admin.ModelAdmin):
    list_display = ['first_name', 'last_name',
                    'address_street', 'telephone_number', 'date_of_birth', 'verification_stage_display']
    search_fields = ['first_name', 'last_name',
                     'address_street', 'telephone_number', 'date_of_birth']
    list_filter = [VerificationLevelFilter]


@admin.register(CompanyProfile)
class CompanyProfile(admin.ModelAdmin):
    list_display = ['name', 'uid',
                    'address_street', 'verification_stage_display']
    search_fields = ['name', 'uid',
                     'address_street']
    list_filter = [VerificationLevelFilter]
