from django.contrib import admin

from apps.verification.models import (CompanyVerification, UserVerification,
                                      VerificationEntry, VerificationInput,
                                      VerificationInputData)
from apps.wallet.utils import create_claim_transaction


def approve_verification(modeladmin, request, queryset):
    updated = 0
    transactions_created = 0
    for obj in queryset:
        if obj.state == VERIFICATION_STATES.CLAIMED.value:
            continue
        if not obj.receiving_wallet:
            continue
        obj.state = VERIFICATION_STATES.CLAIMED.value
        obj.receiving_wallet.state = WALLET_STATES.VERIFIED.value

        obj.receiving_wallet.save()

        if obj.receiving_wallet.category == WALLET_CATEGORIES.CONSUMER.value:
            create_claim_transaction(wallet)
            transactions_created += 1

        obj.save()
        updated += 1

    self.message_user(request, ngettext(
        '%d entry updated.',
        '%d entries updated.',
        updated,
    ) % updated, messages.SUCCESS)

    self.message_user(request, ngettext(
        '%d entry updated.',
        '%d entries updated.',
        transactions_created,
    ) % transactions_created, messages.SUCCESS)


approve_verification.short_description = 'Approve selected verification entries and transfer money'


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'currency', 'state']
    list_filter = (
        'currency', 'state'
    )
    search_fields = ['name', 'address']

    actions = [approve_verification]

    class Meta:
        model = UserVerification


@admin.register(CompanyVerification)
class CompanyVerificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'uid', 'currency', 'state']
    list_filter = ['currency', 'state']
    search_fields = ['name', 'address']
    actions = [approve_verification]

    class Meta:
        model = CompanyVerification


# admin.site.register(VerificationEntry)
# admin.site.register(VerificationInput)
# admin.site.register(VerificationInputData)
