from django.core.exceptions import ValidationError
from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.verification.models import UserVerification, CompanyVerification, VERIFICATION_STATES


@receiver(pre_save, sender=CompanyVerification, dispatch_uid='custom_company_verification_validation')
def custom_company_verification_validation(sender, instance, **kwargs):
    if not instance.uid and not (instance.owner_name and instance.owner_address and instance.owner_telephone_number):
        raise ValidationError(
            "Either uid or owner information has to be filled out")
    if instance.state != VERIFICATION_STATES.OPEN.value and not instance.receiving_wallet:
        raise ValidationError(
            "With this state the receiving_wallet needs to be set")


@receiver(pre_save, sender=UserVerification, dispatch_uid='custom_user_verification_validation')
def custom_user_verification_validation(sender, instance, **kwargs):
    if instance.state != VERIFICATION_STATES.OPEN.value and not instance.receiving_wallet:
        raise ValidationError(
            "With this state the receiving_wallet needs to be set")
