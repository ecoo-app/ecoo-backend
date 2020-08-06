from django.contrib import admin, messages
from apps.wallet.models import CashOutRequest,  WalletPublicKeyTransferRequest, Company, Transaction, MetaTransaction, Wallet, OwnerWallet, TRANSACTION_STATES
from django.utils.translation import ugettext_lazy as _
import requests
from django.conf import settings
from django import forms
import datetime
from django.shortcuts import render


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
