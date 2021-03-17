from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from project.mixins import UUIDModel


class Currency(UUIDModel):
    name = models.CharField(verbose_name=_("Name"), max_length=32)
    symbol = models.CharField(verbose_name=_("Symbol"), max_length=5, default="")
    token_id = models.IntegerField(verbose_name=_("Token Id"))
    decimals = models.IntegerField(verbose_name=_("Decimals"), default=0)

    allow_minting = models.BooleanField(verbose_name=_("Allow minting"), default=True)
    campaign_end = models.DateField(verbose_name=_("Campaign end"), null=True)
    claim_deadline = models.DateField(verbose_name=_("Claim deadline"), null=True)
    starting_capital = models.IntegerField(
        verbose_name=_("Starting capital"), default=10, blank=False, null=False
    )
    max_claims = models.IntegerField(verbose_name=_("Max claims"), default=5)

    owner_wallet = models.ForeignKey(
        "wallet.OwnerWallet",
        null=True,
        editable=False,
        on_delete=models.DO_NOTHING,
        related_name="owner_currencies",
    )

    cashout_wallet = models.ForeignKey(
        "wallet.Wallet",
        null=True,
        blank=True,
        editable=True,
        on_delete=models.DO_NOTHING,
        related_name="cashout_currencies",
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)
    is_public = models.BooleanField(verbose_name=_("Is public"), default=False)

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        permissions = [("can_view_all_currencies", "Can view all currencies")]

    @staticmethod
    def get_currencies_to_user(user):
        if user.has_perm("currency.can_view_all_currencies") or user.is_superuser:
            return Currency.objects.all()
        return Currency.objects.filter(users__id__exact=user.pk)

    # TODO: additional fields?
    def __str__(self):
        return self.name


class PayoutAccount(UUIDModel):
    currency = models.OneToOneField(Currency, null=True, on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_("Account name"), max_length=32)
    bank_clearing_number = models.CharField(
        verbose_name=_("clearing number"), max_length=32
    )
    iban = models.CharField(verbose_name=_("IBAN"), max_length=255)
    payout_notes = models.CharField(max_length=64, verbose_name=_("Notes for payout"))

    class Meta:
        verbose_name = _("PayoutAccount")
        verbose_name_plural = _("PayoutAccounts")
