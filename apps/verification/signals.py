from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from apps.verification.models import UserVerification, CompanyVerification, AddressPinVerification, SMSPinVerification, VERIFICATION_STATES
from apps.verification.utils import send_sms, send_postcard
import random
import string
import traceback

system_random = random.SystemRandom()


@receiver(pre_save, sender=SMSPinVerification, dispatch_uid='custom_sms_pin_verification_validation')
def custom_sms_pin_verification_validation(sender, instance, **kwargs):
    if not instance.pin:
        instance.pin = ''.join(system_random.choice(
            string.digits) for x in range(6))
        try:
            success, payload = send_sms(
                to_number=instance.user_profile.telephone_number,
                message="{} {}".format(instance.pin, settings.SMS_TEXT)
            )
            if success:
                instance.external_id = payload
            else:
                instance.notes = payload
        except Exception as error:
            instance.notes = 'Exception during sync: {}\nTraceback: {}'.format(
                repr(error), traceback.format_exc())


@ receiver(pre_save, sender=AddressPinVerification, dispatch_uid='custom_address_pin_verification_validation')
def custom_address_pin_verification_validation(sender, instance, **kwargs):
    if not instance.pin:
        instance.pin = ''.join(system_random.choice(
            string.digits) for x in range(6))
        try:
            success, payload = send_postcard(
                message=settings.POST_CARD_TEXT.format(
                    instance.company_profile.wallet.wallet_id, instance.pin),
                company=instance.company_profile.name,
                street=instance.company_profile.address_street,
                zip=instance.company_profile.address_postal_code,
                city=instance.company_profile.address_town,
            )
            if success:
                instance.external_id = payload
            else:
                instance.notes = payload

        except Exception as error:
            instance.notes = 'Exception during sync: {}\nTraceback: {}'.format(
                repr(error), traceback.format_exc())
