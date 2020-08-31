from django.contrib import admin
from django.conf.urls import url
from django.db import transaction
from io import StringIO
from apps.verification.models import (CompanyVerification, UserVerification,
                                      AddressPinVerification, SMSPinVerification)
from apps.wallet.utils import create_claim_transaction
from apps.verification.forms import ImportForm
from django.template.response import TemplateResponse
from django.contrib import messages
from django.http import HttpResponseRedirect
from apps.verification.filters import VerificaitonFilter
from django.utils.translation import gettext as _
import csv


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
        _('%d entry updated.'),
        _('%d entries updated.'),
        updated,
    ) % updated, messages.SUCCESS)

    self.message_user(request, ngettext(
        _('%d entry updated.'),
        _('%d entries updated.'),
        transactions_created,
    ) % transactions_created, messages.SUCCESS)


approve_verification.short_description = _(
    'Approve selected verification entries and transfer money')


class ImportMixin:
    def import_csv(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied

        form = ImportForm()
        if request.method == 'POST':
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                def is_row_valid(x): return all((row.get(x) != None and row.get(
                    x) != '') for x in self.import_validate_fields)
                csv_reader = csv.DictReader(
                    StringIO(form.cleaned_data['csv_file'].read().decode('UTF-8')))
                created, line_number = 0, 1
                with transaction.atomic():
                    for row in csv_reader:
                        line_number += 1
                        if not is_row_valid(row):
                            form.add_error('csv_file', _(
                                'Line Nr {} is invalid:{}').format(str(line_number), row))
                            transaction.set_rollback(True)
                            break
                        user_verification = UserVerification(**row)
                        user_verification.save()
                        created += 1

                    if form.is_valid():
                        messages.add_message(
                            request, messages.SUCCESS, '{} Objects created'.format(created))
                        return HttpResponseRedirect(request.META['HTTP_REFERER'])
        return TemplateResponse(request, 'admin/import_csv.html', {'form': form, 'opts': self.opts, 'media': self.media, 'title': 'Import', 'import_validate_fields': self.import_validate_fields, 'import_name': self.import_name})

    def get_extra_urls(self):
        return [
            url(r'^' + self.import_name.replace('_', '-') + '/$',
                self.admin_site.admin_view(self.import_csv), name=self.import_name),
        ]


@admin.register(UserVerification)
class UserVerificationAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'address_street',
                    'address_town', 'address_postal_code', 'date_of_birth', 'state']
    list_filter = ['state']
    search_fields = ['first_name', 'last_name', 'address_street',
                     'address_town', 'address_postal_code', 'date_of_birth']

    import_name = 'user_import'
    import_validate_fields = ['first_name',
                              'last_name', 'address_street', 'date_of_birth']

    class Meta:
        model = UserVerification

    def get_urls(self):
        return self.get_extra_urls() + super(UserVerificationAdmin, self).get_urls()


@admin.register(CompanyVerification)
class CompanyVerificationAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ['name', 'uid', 'state']
    list_filter = ['state']
    search_fields = ['name', 'uid']

    import_name = 'company_import'
    import_validate_fields = ['name', 'uid']

    class Meta:
        model = CompanyVerification

    def get_urls(self):
        return self.get_extra_urls() + super(CompanyVerificationAdmin, self).get_urls()


@admin.register(SMSPinVerification)
class SMSPinVerificationAdmin(admin.ModelAdmin):
    readonly_fields = ['user_profile', 'pin']
    list_display = ['user_profile', 'pin', 'state']


@admin.register(AddressPinVerification)
class AddressPinVerificationAdmin(admin.ModelAdmin):
    readonly_fields = ['company_profile', 'pin']
    list_display = ['company_profile', 'pin', 'state', 'preview_link']
