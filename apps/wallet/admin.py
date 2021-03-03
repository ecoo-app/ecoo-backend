import datetime
import json
from io import BytesIO
from typing import Optional

import pyqrcode
import pysodium
import pytezos
import requests
import weasyprint
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import (FileResponse, HttpRequest, HttpResponse,
                         HttpResponseRedirect)
from django.shortcuts import render
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from weasyprint import CSS

from apps.wallet.forms import GenerateWalletForm
from apps.wallet.models import (TRANSACTION_STATES, WALLET_CATEGORIES,
                                CashOutRequest, MetaTransaction, OwnerWallet,
                                PaperWallet, Transaction, Wallet,
                                WalletPublicKeyTransferRequest)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    readonly_fields = ['wallet_id', 'created_at']
    fields = ['currency', 'wallet_id', 'category',
              'owner', 'public_key', 'state', 'created_at']
    list_display = ['wallet_id', 'owner', 'balance',
                    'nonce', 'state', 'category', 'address', 'currency', 'created_at']
    list_filter = ['currency', 'category', 'state', 'created_at']
    search_fields = ['wallet_id', 'owner__username']

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(OwnerWallet)
class OwnerWalletAdmin(WalletAdmin):
    pass


def get_pdf(modeladmin, request, queryset):
    documents = []
    response = HttpResponse(content_type="application/pdf")

    for wallet in queryset.all():
        encryption_key = bytes.fromhex(settings.ENCRYPTION_KEY)
        nonce = pysodium.randombytes(pysodium.crypto_secretbox_NONCEBYTES)
        pk = pysodium.crypto_aead_xchacha20poly1305_ietf_encrypt(
            wallet.private_key.encode('UTF-8'), None, nonce, encryption_key)
        decrypted_pk = pysodium.crypto_aead_xchacha20poly1305_ietf_decrypt(
            pk, None, nonce, encryption_key)

        payload = {
            'nonce': nonce.hex(),
            'id': wallet.wallet_id,
            'pk': pk.hex()
        }

        qr_code = pyqrcode.create(json.dumps(payload), error='M')

        template = get_template('wallet/paper_wallet_pdf.html')
        html = template.render({'image': qr_code.png_as_base64_str(scale=5
                                                                   ), 'logo': settings.STATIC_ROOT+'/wallet/ecoo_logo_bw.png', 'wetzikon_bw': settings.STATIC_ROOT+'/wallet/wetzikon_bw.png'}, request)  # .encode(encoding="UTF-8")

        documents.append(weasyprint.HTML(
            string=html, base_url=request.build_absolute_uri()).write_pdf(
                target=response,
                presentational_hints=True,
                stylesheets=[CSS(settings.STATIC_ROOT + '/wallet/print.css')]
        ))

    return response


get_pdf.short_description = _('Download QR-Code pdf')


@admin.register(PaperWallet)
class PaperWalletAdmin(WalletAdmin):
    actions = [get_pdf]

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
                    i += 1
                    self.generate_wallet(currency)
                    print(str(i) + ' wallet generated')

                if form.is_valid():
                    messages.add_message(request, messages.SUCCESS, _(
                        '{} Wallets generated').format(amount))
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])

        return TemplateResponse(request, 'admin/generate_wallets.html', {'form': form, 'opts': self.opts, 'media': self.media, })

    def generate_wallet(self, currency):
        key = pytezos.crypto.key.Key.generate()
        private_key = key.secret_key(None, False)
        public_key = key.public_key()

        retry = True
        while retry:
            try:
                owner_wallet = PaperWallet.objects.create(currency=currency, private_key=private_key, wallet_id=PaperWallet.generate_wallet_id(
                ), public_key=public_key, category=WALLET_CATEGORIES.CONSUMER.value)
                retry = False
            except IntegrityError:
                retry = True


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ['submitted_to_chain_at',
                       'operation_hash', 'notes', 'created_at']
    list_display = ['from_wallet', 'to_wallet',
                    'amount', 'state', 'created_at']
    list_filter = ['from_wallet__currency', 'state', 'created_at']
    search_fields = ['from_wallet__wallet_id', 'to_wallet__wallet_id']
    actions = ['retry_failed', 'force_done']

    def has_delete_permission(self, request, obj=None):
        return False

    def retry_failed(self, request, queryset):
        queryset.filter(state=TRANSACTION_STATES.FAILED.value).update(
            state=TRANSACTION_STATES.OPEN.value)

    retry_failed.short_description = _('Retry failed transactions')

    def force_done(modeladmin, request, queryset):
        queryset.update(
            state=TRANSACTION_STATES.DONE.value)

    force_done.short_description = _('Force transaction to done')


@admin.register(MetaTransaction)
class MetaTransactionAdmin(admin.ModelAdmin):
    readonly_fields = ['submitted_to_chain_at',
                       'operation_hash', 'notes', 'created_at']
    list_display = ['from_wallet', 'to_wallet',
                    'amount', 'state', 'created_at']
    list_filter = ['from_wallet__currency', 'state', 'created_at']
    search_fields = ['from_wallet__wallet_id', 'to_wallet__wallet_id']


@admin.register(WalletPublicKeyTransferRequest)
class WalletPublicKeyTransferRequestAdmin(admin.ModelAdmin):
    readonly_fields = ['submitted_to_chain_at',
                       'operation_hash', 'notes', 'created_at']
    list_display = ['wallet', 'old_public_key',
                    'new_public_key', 'state', 'created_at']
    list_filter = ['state', 'created_at']
    search_fields = ['wallet__wallet_id']


@admin.register(CashOutRequest)
class CashOutRequestAdmin(admin.ModelAdmin):

    class PaymentDateForm(forms.Form):
        payment_date = forms.DateField(initial=datetime.date.today)

    actions = ['generate_payout_file']
    list_display = ['transaction', 'beneficiary_name',
                    'beneficiary_iban', 'state', 'created_at']
    list_filter = ['state', 'created_at']
    search_fields = [
        'transaction__from_wallet__wallet_id', 'beneficiary_name', ]

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
            if queryset[0].transaction.from_wallet:
                currency = queryset[0].transaction.from_wallet.currency
            else:
                currency = queryset[0].transaction.to_wallet.currency

            form = PaymentDateForm(request.POST)
            if form.is_valid():
                payment_date = form.cleaned_data['payment_date']
                pain_payload = {
                    'from_account': {
                        "name": currency.payoutaccount.name,
                        "bank_clearing_number": currency.payoutaccount.bank_clearing_number,
                        "iban": currency.payoutaccount.iban
                    },
                    'transactions': list(map(lambda cash_out_request: {
                        'amount': cash_out_request.transaction.currency_amount,
                        'payment_date': payment_date.strftime('%Y-%m-%d'),
                        'notes': currency.payoutaccount.payout_notes,
                        'to_account': {
                            'name': cash_out_request.beneficiary_name,
                            'iban': cash_out_request.beneficiary_iban,
                        }
                    }, queryset))
                }
                response = requests.post(
                    "{}/api/v1/generate_xml/".format(settings.PAIN_SERVICE_URL), json=pain_payload, stream=True)

                return FileResponse(BytesIO(response.content), as_attachment=True, filename=f'payout_{datetime.datetime.now().strftime("%Y-%m-%d")}.xml')
            else:
                self.message_user(request, _(
                    'Please enter a correct payment date'), messages.ERROR)
        else:
            form = PaymentDateForm()
            return render(request,
                          'admin/generate_payout_file.html',
                          context={'form': form, 'cash_out_requests': queryset, 'total_amount': sum([tx.transaction.currency_amount for tx in queryset])})

    generate_payout_file.short_description = _('Generate Payout XML')
