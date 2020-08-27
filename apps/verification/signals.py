from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from secrets import token_hex
from apps.verification.models import UserVerification, CompanyVerification, AddressPinVerification, SMSPinVerification, VERIFICATION_STATES
from apps.verification.utils import send_sms, send_postcard


@receiver(pre_save, sender=SMSPinVerification, dispatch_uid='custom_sms_pin_verification_validation')
def custom_sms_pin_verification_validation(sender, instance, **kwargs):
    if not instance.pin:
        instance.pin = token_hex(4)
        send_sms(
            to_number=instance.user_profile.telephone_number, 
            message=
            """{}
            {}""".format(instance.pin, settings.SMS_TEXT)
        )


@receiver(pre_save, sender=AddressPinVerification, dispatch_uid='custom_address_pin_verification_validation')
def custom_address_pin_verification_validation(sender, instance, **kwargs):
    if not instance.pin:
        instance.pin = token_hex(4)
        send_postcard(
            message=instance.pin, 
            company=instance.company_profile.name, 
            street=instance.company_profile.address_street,
            zip=instance.company_profile.address_postal_code,
            city=instance.company_profile.address_town,
        )
