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
from django.http import HttpResponseRedirect, HttpResponse
import pytezos
from django.db import IntegrityError
import zipfile
import base64
import pyqrcode
import pysodium
import os
import json
import uuid

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


    zip_filename = os.path.join(settings.MEDIA_ROOT, 'zip', 'qr_codes_{}.zip'.format(uuid.uuid4()))
    zf = zipfile.ZipFile(zip_filename, 'w')

    for wallet in queryset.all():

        encryption_key = bytes.fromhex(settings.ENCRYPTION_KEY)
        nonce =  os.urandom(24)
        pk = pysodium.crypto_aead_xchacha20poly1305_ietf_encrypt(wallet.private_key, None, nonce, encryption_key)
        
        payload = {
            'nonce': nonce.hex(),
            'id': wallet.wallet_id,
            'pk': pk.hex()
        }

        qr_code = pyqrcode.create(json.dumps(payload))
        filename = os.path.join(settings.MEDIA_ROOT, 'qr', wallet.wallet_id + '.png') 
        qr_code.png(filename, scale=5)
        zf.write(filename)
    zf.close()

    zip_file = open(zip_filename,'rb').read()
    return HttpResponse(zip_file, content_type = "application/zip")

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
