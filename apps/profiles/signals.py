from django.core.exceptions import ValidationError
from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.profiles.models import CompanyProfile, UserProfile
from apps.verification.models import CompanyVerification, UserVerification, SMSPinVerification, AddressPinVerification, VERIFICATION_STATES


@receiver(post_save, sender=CompanyProfile, dispatch_uid='custom_company_profile_validation')
def custom_company_profile_validation(sender, instance, **kwargs):
    if not instance.uid:
        raise ValidationError(
            "Either uid or owner information has to be filled out")
    if CompanyVerification.objects.exclude(state=VERIFICATION_STATES.CLAIMED.value).filter(name=instance.name, uid=instance.uid).exists():
        company_verification = CompanyVerification.objects.get(
            name=instance.name, uid=instance.uid)
        company_verification.company_profile = instance
        company_verification.state = VERIFICATION_STATES.PENDING.value
        company_verification.save()

        address_pin_verification = AddressPinVerification.objects.create(company_profile=instance,
                                                                         state=VERIFICATION_STATES.PENDING.value)


@receiver(post_save, sender=UserProfile, dispatch_uid='custom_user_profile_validation')
def custom_user_profile_validation(sender, instance, **kwargs):
    if not instance.telephone_number.startswith("+417"):
        raise ValidationError(
            "Only Swiss mobile numbers are allowed")
    if UserVerification.objects.exclude(state=VERIFICATION_STATES.CLAIMED.value).filter(first_name=instance.first_name, last_name=instance.last_name,
                                                                                        address_street=instance.address_street, address_town=instance.address_town,
                                                                                        address_postal_code=instance.address_postal_code, date_of_birth=instance.date_of_birth).exists():
        user_verification = UserVerification.objects.get(first_name=instance.first_name, last_name=instance.last_name,
                                                         address_street=instance.address_street, address_town=instance.address_town,
                                                         address_postal_code=instance.address_postal_code, date_of_birth=instance.date_of_birth)
        user_verification.user_profile = instance
        user_verification.state = VERIFICATION_STATES.PENDING.value
        user_verification.save()

        SMSPinVerification.objects.create(
            user_profile=instance, state=VERIFICATION_STATES.PENDING.value)
