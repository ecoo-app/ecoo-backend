from django.contrib import admin
from django.conf.urls import url
from django.db import transaction
from io import StringIO
from apps.verification.models import AddressPinVerification, CompanyVerification, PlaceOfOrigin, SMSPinVerification, UserVerification, VERIFICATION_STATES
from apps.wallet.utils import create_claim_transaction
from apps.verification.forms import ImportForm
from django.template.response import TemplateResponse
from django.contrib import messages
from django.http import HttpResponseRedirect
from apps.verification.filters import VerificaitonFilter
from django.utils.translation import gettext as _, ngettext
from django.utils.safestring import mark_safe

import csv
from django.urls import reverse
from apps.wallet.models import PaperWallet, WALLET_CATEGORIES, WALLET_STATES
from django.core.exceptions import PermissionDenied
from django import forms
from django.forms.models import BaseInlineFormSet

# TODO: ths isn't used anymore, should it be fixed and used or removed?


def approve_verification(modeladmin, request, queryset):
    updated = 0
    transactions_created = 0
    for obj in queryset:
        if obj.state == VERIFICATION_STATES.CLAIMED.value:
            continue
        # TODO: this field has been removed
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

    modeladmin.message_user(request, ngettext(
        _('%d entry updated.'),
        _('%d entries updated.'),
        updated,
    ) % updated, messages.SUCCESS)

    modeladmin.message_user(request, ngettext(
        _('%d entry updated.'),
        _('%d entries updated.'),
        transactions_created,
    ) % transactions_created, messages.SUCCESS)


approve_verification.short_description = _(
    'Approve selected verification entries and transfer money')


class ImportMixin:
    additional_import_fields = []

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

                        places_of_origin = []
                        for k in ['place_of_origin1', 'place_of_origin2', 'place_of_origin3']:
                            if row.get(k) != None:
                                places_of_origin.append(
                                    PlaceOfOrigin(place_of_origin=row.get(k)))
                                del(row[k])

                        entry = self.model(**row)
                        entry.save()

                        for p in places_of_origin:
                            p.user_verification = entry
                            p.save()
                        created += 1

                    if form.is_valid():
                        messages.add_message(
                            request, messages.SUCCESS, '{} Objects created'.format(created))
                        return HttpResponseRedirect(request.META['HTTP_REFERER'])
        return TemplateResponse(request, 'admin/import_csv.html', {'form': form, 'opts': self.opts, 'media': self.media, 'title': 'Import', 'import_validate_fields': self.import_validate_fields + self.additional_import_fields, 'import_name': self.import_name})

    def get_extra_urls(self):
        return [
            url(r'^' + self.import_name.replace('_', '-') + '/$',
                self.admin_site.admin_view(self.import_csv), name=self.import_name),
        ]

class AtLeastOneRequiredInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super(AtLeastOneRequiredInlineFormSet, self).clean()
        if any(self.errors):
            return
        if not any(cleaned_data and not cleaned_data.get('DELETE', False)
            for cleaned_data in self.cleaned_data):
            raise forms.ValidationError(_('At least one item required.'))    

class PlaceOfOriginInline(admin.TabularInline):
    model = PlaceOfOrigin
    extra = 1
    formset = AtLeastOneRequiredInlineFormSet


@admin.register(UserVerification)
class UserVerificationAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'address_street',
                    'address_town', 'address_postal_code', 'date_of_birth', 'state', 'create_paper_wallet', 'created_at']
    list_filter = ['state', 'created_at']
    search_fields = ['first_name', 'last_name', 'address_street',
                     'address_town', 'address_postal_code', 'date_of_birth']
    inlines = [PlaceOfOriginInline, ]

    import_name = 'user_import'
    import_validate_fields = ['first_name',
                              'last_name', 'address_street', 'address_town', 'address_postal_code', 'date_of_birth']
    additional_import_fields = ['place_of_origin1',
                                'place_of_origin2', 'place_of_origin3']
    readonly_fields = ['created_at', ]

    class Meta:
        model = UserVerification

    def get_urls(self):
        return self.get_extra_urls() + super(UserVerificationAdmin, self).get_urls()

    def create_paper_wallet(self, obj):
        if obj.state == VERIFICATION_STATES.OPEN.value:
            return mark_safe(u"<a class='button btn-success' href='{}'>{}</a>".format(reverse('verification:generate_paper_wallet', args=(obj.uuid,)), _('create paper wallet')))
        return mark_safe(u"<a class='btn-info'>{}</a>".format(_('cannot create paper wallet')))

    create_paper_wallet.short_description = _('paper wallet')
    create_paper_wallet.allow_tags = True


@admin.register(CompanyVerification)
class CompanyVerificationAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ['name', 'uid', 'state', 'created_at']
    list_filter = ['state', 'created_at']
    search_fields = ['name', 'uid']

    import_name = 'company_import'
    import_validate_fields = [
        'name', 'uid', 'address_street', 'address_town', 'address_postal_code']
    readonly_fields = ['created_at', 'notes']

    class Meta:
        model = CompanyVerification

    def get_urls(self):
        return self.get_extra_urls() + super(CompanyVerificationAdmin, self).get_urls()


@admin.register(SMSPinVerification)
class SMSPinVerificationAdmin(admin.ModelAdmin):
    readonly_fields = ['user_profile', 'pin', 'created_at']
    list_display = ['user_profile', 'pin', 'state', 'created_at']

    readonly_fields = ['created_at', 'notes']


@admin.register(AddressPinVerification)
class AddressPinVerificationAdmin(admin.ModelAdmin):
    readonly_fields = ['company_profile', 'pin', 'created_at']
    list_display = ['company_profile', 'pin',
                    'state', 'preview_link', 'created_at']

    readonly_fields = ['created_at', 'external_id', 'notes']


@admin.register(PlaceOfOrigin)
class PlaceOfOriginAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at']
    list_display = ['user_verification', 'place_of_origin']
