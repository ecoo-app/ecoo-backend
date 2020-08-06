from enum import Enum

from django.db import models

from project.mixins import UUIDModel


class Currency(UUIDModel):
    name = models.CharField(max_length=32)
    symbol = models.CharField(max_length=5, default="")
    token_id = models.IntegerField()
    decimals = models.IntegerField(default=0)

    allow_minting = models.BooleanField(default=True)
    campaign_end = models.DateField(null=True)
    claim_deadline = models.DateField(null=True)
    starting_capital = models.IntegerField(default=10, blank=False, null=False)
    max_claims = models.IntegerField(default=5)

    owner_wallet = models.ForeignKey(
        "wallet.OwnerWallet", null=True, editable=False, on_delete=models.DO_NOTHING, related_name="currencies")

    class Meta:
        verbose_name_plural = 'Currencies'

    # TODO: additional fields?
    def __str__(self):
        return self.name
