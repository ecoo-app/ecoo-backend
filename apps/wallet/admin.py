import datetime
import os
import uuid
import zipfile
from io import BytesIO

import pyqrcode
import requests
import weasyprint
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from PIL import Image
from weasyprint import CSS

from apps.currency.filters import CurrencyOwnedFilter
from apps.currency.mixins import CurrencyOwnedAdminMixin
from apps.currency.models import Currency
from apps.wallet.forms import GenerateWalletForm, TransactionAdminForm
from apps.wallet.models import (
    TRANSACTION_STATES,
    CashOutRequest,
    MetaTransaction,
    OwnerWallet,
    PaperWallet,
    Transaction,
    Wallet,
    WalletPublicKeyTransferRequest,
)


@admin.register(Wallet)
class WalletAdmin(CurrencyOwnedAdminMixin, admin.ModelAdmin):
    readonly_fields = ["wallet_id", "created_at"]
    fields = [
        "currency",
        "wallet_id",
        "category",
        "owner",
        "public_key",
        "state",
        "created_at",
    ]
    list_display = [
        "wallet_id",
        "owner",
        "balance",
        "nonce",
        "state",
        "category",
        "address",
        "currency",
        "created_at",
    ]
    list_filter = [CurrencyOwnedFilter, "category", "state", "created_at"]
    search_fields = ["wallet_id", "owner__username"]

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(OwnerWallet)
class OwnerWalletAdmin(WalletAdmin):
    pass


@admin.register(PaperWallet)
class PaperWalletAdmin(WalletAdmin):
    actions = ["get_pdf", "download_zip", "download_links_pdf"]

    def generate_wallets(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied

        form = GenerateWalletForm()
        if request.method == "POST":
            form = GenerateWalletForm(request.POST, request.FILES)
            if form.is_valid():
                amount = form.cleaned_data["amount"]
                currency = form.cleaned_data["currency"]

                for i in range(amount):
                    i += 1
                    self.generate_wallet(currency)
                    print(str(i) + " wallet generated")

                if form.is_valid():
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        _("{} Wallets generated").format(amount),
                    )
                    return HttpResponseRedirect(request.META["HTTP_REFERER"])

        return TemplateResponse(
            request,
            "admin/generate_wallets.html",
            {
                "form": form,
                "opts": self.opts,
                "media": self.media,
            },
        )

    def get_pdf(modeladmin, request, queryset):
        documents = []
        response = HttpResponse(content_type="application/pdf")

        for wallet in queryset.all():
            qr_code = pyqrcode.create(wallet.generate_deeplink(), error="M")

            template = get_template("wallet/paper_wallet_pdf.html")
            html = template.render(
                {
                    "image": qr_code.png_as_base64_str(scale=5),
                    "logo": settings.STATIC_ROOT + "/wallet/ecoo_logo_bw.png",
                    "wetzikon_bw": settings.STATIC_ROOT + "/wallet/wetzikon_bw.png",
                },
                request,
            )

            documents.append(
                weasyprint.HTML(
                    string=html, base_url=request.build_absolute_uri()
                ).write_pdf(
                    target=response,
                    presentational_hints=True,
                    stylesheets=[CSS(settings.STATIC_ROOT + "/wallet/print.css")],
                )
            )

        return response

    get_pdf.short_description = _("Download QR-Code pdf")

    def download_zip(modeladmin, request, queryset):
        zip_filename = os.path.join(
            settings.MEDIA_ROOT, "zip", "qr_codes_{}.zip".format(uuid.uuid4())
        )
        with zipfile.ZipFile(zip_filename, "w") as zf:
            for wallet in queryset.all():

                qr_code = pyqrcode.create(wallet.generate_deeplink(), error="M")
                filename = os.path.join(
                    settings.MEDIA_ROOT, "qr", wallet.wallet_id + ".png"
                )
                qr_code.png(filename, scale=5)

                img = Image.open(filename)

                img = img.resize((530, 530), Image.ANTIALIAS)
                img.save(filename)

                zf.write(filename)

        zip_file = open(zip_filename, "rb").read()
        return HttpResponse(zip_file, content_type="application/zip")

    download_zip.short_description = _("Download QR-Code Zip")

    def download_links_pdf(self, request, queryset):
        response = HttpResponse(content_type="application/pdf")
        template = get_template("wallet/wallet_deeplinks.html")
        html = template.render(
            {
                "deeplinks": [wallet.generate_deeplink() for wallet in queryset.all()],
            },
            request,
        )

        weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(
            target=response,
            presentational_hints=True,
            stylesheets=[CSS(settings.STATIC_ROOT + "/wallet/print_2.css")],
        )
        return response

    download_links_pdf.short_description = _("Download deeplink(s)")


class TransactionCurrencyFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Currency")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "currency"

    def lookups(self, request, model_admin):
        currencies = Currency.get_currencies_to_user(request.user)

        result = []
        for currency in currencies:
            result.append((str(currency.pk), str(currency)))
        return result

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value() is not None:
            return queryset.filter(
                Q(from_wallet__currency__pk=self.value())
                | Q(to_wallet__currency__pk=self.value())
            )

        return queryset


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = [
        "submitted_to_chain_at",
        "operation_hash",
        "user_notes",
        "notes",
        "created_at",
    ]
    list_display = ["from_wallet", "to_wallet", "amount", "state", "created_at"]
    list_filter = [TransactionCurrencyFilter, "state", "created_at"]
    search_fields = ["from_wallet__wallet_id", "to_wallet__wallet_id"]
    actions = ["retry_failed", "force_done"]
    form = TransactionAdminForm

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not request.user.has_perm("currency.can_view_all_currencies"):
            qs = qs.filter(
                Q(from_wallet__currency__users__id__exact=request.user.id)
                | Q(to_wallet__currency__users__id__exact=request.user.id),
            )
        return qs

    def has_delete_permission(self, request, obj=None):
        return False

    def retry_failed(self, request, queryset):
        queryset.filter(state=TRANSACTION_STATES.FAILED.value).update(
            state=TRANSACTION_STATES.OPEN.value
        )

    retry_failed.short_description = _("Retry failed transactions")

    def force_done(modeladmin, request, queryset):
        queryset.update(state=TRANSACTION_STATES.DONE.value)

    force_done.short_description = _("Force transaction to done")


@admin.register(MetaTransaction)
class MetaTransactionAdmin(admin.ModelAdmin):
    readonly_fields = [
        "submitted_to_chain_at",
        "operation_hash",
        "user_notes",
        "notes",
        "created_at",
    ]
    list_display = ["from_wallet", "to_wallet", "amount", "state", "created_at"]
    list_filter = [TransactionCurrencyFilter, "state", "created_at"]
    search_fields = ["from_wallet__wallet_id", "to_wallet__wallet_id"]
    form = TransactionAdminForm

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not request.user.has_perm("currency.can_view_all_currencies"):
            qs = qs.filter(
                Q(from_wallet__currency__users__id__exact=request.user.id)
                | Q(to_wallet__currency__users__id__exact=request.user.id)
            )
        return qs


@admin.register(WalletPublicKeyTransferRequest)
class WalletPublicKeyTransferRequestAdmin(admin.ModelAdmin):
    readonly_fields = ["submitted_to_chain_at", "operation_hash", "notes", "created_at"]
    list_display = ["wallet", "old_public_key", "new_public_key", "state", "created_at"]
    list_filter = ["state", "created_at"]
    search_fields = ["wallet__wallet_id"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not (
            request.user.has_perm("currency.can_view_all_currencies")
            or request.user.is_superuser
        ):
            qs = qs.filter(wallet__currency__users__id__exact=request.user.id)
        return qs


@admin.register(CashOutRequest)
class CashOutRequestAdmin(admin.ModelAdmin):
    class PaymentDateForm(forms.Form):
        payment_date = forms.DateField(initial=datetime.date.today)

    actions = ["generate_payout_file"]
    list_display = [
        "transaction",
        "beneficiary_name",
        "beneficiary_iban",
        "state",
        "created_at",
    ]
    list_filter = ["state", "created_at"]
    search_fields = [
        "transaction__from_wallet__wallet_id",
        "beneficiary_name",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not (
            request.user.has_perm("currency.can_view_all_currencies")
            or request.user.is_superuser
        ):
            qs = qs.filter(
                transaction__from_wallet__currency__users__id__exact=request.user.id
            )
        return qs

    def generate_payout_file(self, request, queryset):
        class PaymentDateForm(forms.Form):
            payment_date = forms.DateField(initial=datetime.date.today)

        if queryset.exclude(state=TRANSACTION_STATES.OPEN.value).exists():
            self.message_user(
                request,
                _("Only open cashout out requests can be used in this action"),
                messages.ERROR,
            )

        elif queryset.exclude(
            transaction__state=TRANSACTION_STATES.DONE.value
        ).exists():
            self.message_user(
                request,
                _("Only settled (done) transactions can be used in this action"),
                messages.ERROR,
            )

        elif "apply" in request.POST:
            if queryset[0].transaction.from_wallet:
                currency = queryset[0].transaction.from_wallet.currency
            else:
                currency = queryset[0].transaction.to_wallet.currency

            form = PaymentDateForm(request.POST)
            if form.is_valid():
                payment_date = form.cleaned_data["payment_date"]
                pain_payload = {
                    "from_account": {
                        "name": currency.payoutaccount.name,
                        "bank_clearing_number": currency.payoutaccount.bank_clearing_number,
                        "iban": currency.payoutaccount.iban,
                    },
                    "transactions": list(
                        map(
                            lambda cash_out_request: {
                                "amount": cash_out_request.transaction.currency_amount,
                                "payment_date": payment_date.strftime("%Y-%m-%d"),
                                "notes": currency.payoutaccount.payout_notes,
                                "to_account": {
                                    "name": cash_out_request.beneficiary_name,
                                    "iban": cash_out_request.beneficiary_iban,
                                },
                            },
                            queryset,
                        )
                    ),
                }
                response = requests.post(
                    "{}/api/v1/generate_xml/".format(settings.PAIN_SERVICE_URL),
                    json=pain_payload,
                    stream=True,
                )

                return FileResponse(
                    BytesIO(response.content),
                    as_attachment=True,
                    filename=f'payout_{datetime.datetime.now().strftime("%Y-%m-%d")}.xml',
                )
            else:
                self.message_user(
                    request, _("Please enter a correct payment date"), messages.ERROR
                )
        else:
            form = PaymentDateForm()
            return render(
                request,
                "admin/generate_payout_file.html",
                context={
                    "form": form,
                    "cash_out_requests": queryset,
                    "total_amount": sum(
                        [tx.transaction.currency_amount for tx in queryset]
                    ),
                },
            )

    generate_payout_file.short_description = _("Generate Payout XML")
