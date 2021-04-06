import pytezos
from django.contrib import admin
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _

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

    def __generate_paper_wallet(self, currency, category):
        from apps.wallet.models import PaperWallet

        key = pytezos.crypto.key.Key.generate()
        private_key = key.secret_key(None, False)
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
