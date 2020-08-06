from django.contrib import admin, messages
from apps.wallet.models import CashOutRequest,  WalletPublicKeyTransferRequest, Company, Transaction, MetaTransaction, Wallet, OwnerWallet, PaperWallet, TRANSACTION_STATES, WALLET_CATEGORIES
from django.utils.translation import ugettext_lazy as _
import requests
from django.conf import settings
from django import forms
import datetime
from django.shortcuts import render
from django.conf.urls import url
from apps.wallet.forms import GenerateWalletForm
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
import pytezos
from django.db import IntegrityError
import qrcode
import zipfile
import base64
from PIL import Image  
import io
from io import BytesIO, StringIO


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    readonly_fields = ['wallet_id']
    fields = ['currency', 'wallet_id', 'category',
              'owner', 'public_key', 'state']
    list_display = ['wallet_id', 'owner', 'balance',
                    'nonce', 'state', 'category', 'currency']
    list_filter = ['currency', 'category', 'state']


@admin.register(OwnerWallet)
class OwnerWalletAdmin(WalletAdmin):
    exclude = ['company', ]

def download_zip(modeladmin, request, queryset):
    zip_filename = "qr_codes.zip"
    s = StringIO()
    zf = zipfile.ZipFile(s, "w")
    for wallet in queryset.all():
        qr_code = qrcode.make(wallet.private_key)
        zip_path = wallet.wallet_id + '.jpg'
        zf.write(zip_path, qr_code.tobytes())

    zf.close()
    response = HttpResponse(s.getvalue(), mimetype = "application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return response

download_zip.short_description = "Download QR-Code Zip"

@admin.register(PaperWallet)
class PaperWalletAdmin(WalletAdmin):
    exclude = ['company', ]
    actions = [download_zip]


    def get_urls(self):
        return [
            url(r'^generate-wallets/$', self.admin_site.admin_view(self.generate_wallets), name='generate_wallets'),
        ] + super(PaperWalletAdmin, self).get_urls()



    def generate_wallets(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied


        form = GenerateWalletForm()
        if request.method == 'POST':
            form = GenerateWalletForm(request.POST, request.FILES)
            if form.is_valid():
                amount = form.cleaned_data['amount']
                currency = form.cleaned_data['currency']

                for i in range(amount):
                    self.generate_wallet(currency)
                    print(str(i) + ' wallet generated')

                if form.is_valid():
                    messages.add_message(request, messages.SUCCESS, '{} Wallets generated'.format(amount))
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])

        return TemplateResponse(request, 'admin/generate_wallets.html', {'form': form, 'opts': self.opts, 'media': self.media,})

    def generate_wallet(self, currency):
        key = pytezos.crypto.Key.generate()
        private_key = key.secret_key()
        public_key = key.public_key()

        retry = True
        while retry:
            try:
                owner_wallet = PaperWallet.objects.create(currency=currency, private_key=private_key, wallet_id=PaperWallet.generate_wallet_id(), public_key=public_key, category=WALLET_CATEGORIES.CONSUMER.value)
                retry = False
            except IntegrityError:
                retry = True






@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ['submitted_to_chain_at', 'operation_hash', 'notes']
    list_display = ['from_wallet', 'to_wallet', 'amount', 'state']
    list_filter = ['from_wallet__currency', 'state']
    search_fields = ['from_wallet__wallet_id', 'to_wallet__wallet_id']


@admin.register(MetaTransaction)
class MetaTransactionAdmin(admin.ModelAdmin):
    readonly_fields = ['submitted_to_chain_at', 'operation_hash', 'notes']
    list_display = ['from_wallet', 'to_wallet', 'amount', 'state']
    list_filter = ['from_wallet__currency', 'state']
    search_fields = ['from_wallet__wallet_id', 'to_wallet__wallet_id']


@admin.register(WalletPublicKeyTransferRequest)
class WalletPublicKeyTransferRequestAdmin(admin.ModelAdmin):
    readonly_fields = ['submitted_to_chain_at', 'operation_hash', 'notes']
    list_display = ['wallet', 'old_public_key', 'new_public_key', 'state']
    list_filter = ['wallet', 'state']
    search_fields = ['wallet__wallet_id']


@admin.register(CashOutRequest)
class CashOutRequestAdmin(admin.ModelAdmin):

    class PaymentDateForm(forms.Form):
        payment_date = forms.DateField(initial=datetime.date.today)

    actions = ['generate_payout_file']
    list_display = ['transaction', 'beneficiary_name',
                    'beneficiary_iban', 'state']
    list_filter = ['transaction__state', 'state']
    search_fields = [
        'transaction__from_wallet__wallet_id', 'beneficiary_name']

    def generate_payout_file(self, request, queryset):
        class PaymentDateForm(forms.Form):
            payment_date = forms.DateField(initial=datetime.date.today)

        if queryset.exclude(state=TRANSACTION_STATES.OPEN.value).exists():
            self.message_user(request, _(
                'Only open cashout out requests can be used in this action'), messages.ERROR)
        elif queryset.exclude(transaction__state=TRANSACTION_STATES.DONE.value).exists():
            self.message_user(request, _(
                'Only settled (done) transactions can be used in this action'), messages.ERROR)
        elif 'apply' in request.POST:
            form = PaymentDateForm(request.POST)
            if form.is_valid():
                payment_date = form.cleaned_data['payment_date']
                pain_payload = {
                    'from_account': {

                    },
                    'transactions': map(lambda cash_out_request: {
                        'amount': cash_out_request.transaction.amount,
                        'payment_date': payment_date,
                        'to_account': {
                            'name': cash_out_request.beneficiary_name,
                            'iban': cash_out_request.beneficiary_iban
                        }
                    }, queryset)
                }
                requests.post(
                    "{}/api/v1/generate_xml/".format(settings.PAIN_SERVICE_URL), json=pain_payload)
            else:
                self.message_user(request, _(
                    'Please enter a correct payment date'), messages.ERROR)
        else:
            form = PaymentDateForm()
            return render(request,
                          'admin/generate_payout_file.html',
                          context={'form': form, 'cash_out_requests': queryset})

    generate_payout_file.short_description = 'Generate Payout XML'


# TODO: add proper admin sites
admin.site.register(Company)
