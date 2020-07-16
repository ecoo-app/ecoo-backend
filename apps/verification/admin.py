from django.contrib import admin
from apps.verification.models import VerificationEntry, VerificationInput, VerificationInputData

# @admin.register(Currency)

admin.site.register(VerificationEntry)
admin.site.register(VerificationInput)
admin.site.register(VerificationInputData)