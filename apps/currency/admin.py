import pytezos
from django.contrib import admin
from django.contrib.messages import constants as message_constants
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _

from apps.currency.forms import PaperWalletCreateForm
from apps.currency.models import Currency, PayoutAccount
from apps.wallet.utils import create_claim_transaction


class PayoutAccountInline(admin.StackedInline):
    model = PayoutAccount
    fields = [
        "name",
        "iban",
        "bank_clearing_number",
        "payout_notes",
    ]


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    inlines = [PayoutAccountInline]
    filter_horizontal = ("users",)

    list_display = [
        "name",
        "token_id",
        "symbol",
        "decimals",
        "allow_minting",
        "campaign_end",
        "created_at",
    ]
    list_filter = ["allow_minting", "created_at"]
    readonly_fields = [
        "created_at",
    ]
    actions = [
        "generate_paper_wallet_consumer",
        "generate_paper_wallet_company",
        "generate_multiple_consumer_paper_wallets",
        "generate_multiple_company_paper_wallets",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if not (
            request.user.has_perm("currency.can_view_all_currencies")
            or request.user.is_superuser
        ):
            qs = qs.filter(users__id__exact=request.user.id)
        return qs

    def generate_paper_wallet_consumer(modeladmin, request, currencies):
        from apps.wallet.models import WALLET_CATEGORIES

        currency = currencies.first()

        paper_wallet = modeladmin.__generate_paper_wallet(
            currency=currency, category=WALLET_CATEGORIES.CONSUMER.value
        )
        create_claim_transaction(paper_wallet)
        return HttpResponseRedirect(
            reverse("admin:wallet_paperwallet_change", args=[paper_wallet.pk])
        )

    generate_paper_wallet_consumer.short_description = _(
        "generate paperwallet for consumer"
    )

    def generate_paper_wallet_company(modeladmin, request, currencies):
        from apps.wallet.models import WALLET_CATEGORIES

        currency = currencies.first()

        paper_wallet = modeladmin.__generate_paper_wallet(
            currency=currency, category=WALLET_CATEGORIES.COMPANY.value
        )

        return HttpResponseRedirect(
            reverse("admin:wallet_paperwallet_change", args=[paper_wallet.pk])
        )

    generate_paper_wallet_company.short_description = _(
        "generate paperwallet for a company"
    )

    def generate_multiple_company_paper_wallets(self, request, currencies):
        from apps.wallet.models import WALLET_CATEGORIES
        currency = currencies.first()
        if "apply" in request.POST:  # if user pressed 'apply' on intermediate page
            n = int(request.POST.get("number_of_wallets", "0"))

            for i in range(n):
                try:
                    paper_wallet = self.__generate_paper_wallet(
                        currency=currency,
                        category=int(request.POST.get("_type_of_wallet", "0")),
                    )
                    create_claim_transaction(paper_wallet)
                except ValidationError as e:
                    self.message_user(
                        request,
                        "Error: %s" % str(e.message),
                        level="error",
                    )

            self.message_user(request, "Created %s paper wallets" % str(n))
            return HttpResponseRedirect(request.get_full_path())

        form = PaperWalletCreateForm(
            initial={
                "_currency": currency.pk,
                "_type_of_wallet": WALLET_CATEGORIES.COMPANY.value,
            }
        )

        return render(
            request,
            "admin/currency/create_paper_wallets.html",
            {"form": form, "currency": currency},
        )

    generate_multiple_company_paper_wallets.short_description = _(
        "generate multiple company paperwallet"
    )

    def generate_multiple_consumer_paper_wallets(self, request, currencies):
        from apps.wallet.models import WALLET_CATEGORIES
        currency = currencies.first()
        if "apply" in request.POST:  # if user pressed 'apply' on intermediate page
            n = int(request.POST.get("number_of_wallets", "0"))

            if n * currency.starting_capital > currency.owner_wallet.balance:
                self.message_user(
                    request,
                    "Not enough balance on owner wallet",
                    level=message_constants.ERROR,
                )
                return HttpResponseRedirect(request.get_full_path())

            for i in range(n):

                try:
                    paper_wallet = self.__generate_paper_wallet(
                        currency=currency,
                        category=int(request.POST.get("_type_of_wallet", "0")),
                    )
                    create_claim_transaction(paper_wallet)
                except ValidationError as e:
                    self.message_user(
                        request,
                        "Error: %s" % str(e.message),
                        level="error",
                    )

            self.message_user(request, "Created %s paper wallets" % str(n))
            return HttpResponseRedirect(request.get_full_path())

        form = PaperWalletCreateForm(
            initial={
                "_currency": currency.pk,
                "_type_of_wallet": WALLET_CATEGORIES.CONSUMER.value,
            }
        )

        return render(
            request,
            "admin/currency/create_paper_wallets.html",
            {"form": form, "currency": currency},
        )

    generate_multiple_consumer_paper_wallets.short_description = _(
        "generate multiple consumer paperwallet"
    )

    def __generate_paper_wallet(self, currency, category):
        from apps.wallet.models import PaperWallet

        key = pytezos.crypto.key.Key.generate()
        private_key = key.secret_key()
        public_key = key.public_key()

        retry = True
        while retry:
            try:
                paper_wallet = PaperWallet.objects.create(
                    currency=currency,
                    private_key=private_key,
                    wallet_id=PaperWallet.generate_wallet_id(),
                    public_key=public_key,
                    category=category,
                )
                retry = False
            except IntegrityError:
                retry = True
        return paper_wallet

    def render_change_form(self, request, context, *args, **kwargs):
        from apps.wallet.models import OwnerWallet

        if kwargs.get("obj", None):
            context["adminform"].form.fields[
                "cashout_wallet"
            ].queryset = OwnerWallet.objects.filter(currency=kwargs["obj"])
        else:
            context["adminform"].form.fields[
                "cashout_wallet"
            ].queryset = OwnerWallet.objects.none()
        return super().render_change_form(request, context, *args, **kwargs)
