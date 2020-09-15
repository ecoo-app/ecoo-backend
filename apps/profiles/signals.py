from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.profiles.models import CompanyProfile, UserProfile
from apps.verification.models import CompanyVerification, UserVerification, SMSPinVerification, AddressPinVerification, VERIFICATION_STATES


@receiver(post_save, sender=CompanyProfile, dispatch_uid='custom_company_profile_validation')
def custom_company_profile_validation(sender, instance, **kwargs):
    if instance.address_street and instance.address_postal_code and instance.address_town and instance.name and instance.uid:
        company_verifications = CompanyVerification.objects.exclude(state=VERIFICATION_STATES.CLAIMED.value).filter(
            address_street__iexact=instance.address_street,
            address_postal_code=instance.address_postal_code,
            address_town__iexact=instance.address_town,
            name__iexact=instance.name,
            uid__iexact=instance.uid,
        )
        if company_verifications.exists():
            company_verification = company_verifications[0]
            company_verification.company_profile = instance
            company_verification.state = VERIFICATION_STATES.PENDING.value
            company_verification.save()

            address_pin_verification = AddressPinVerification.objects.create(
                company_profile=instance, state=VERIFICATION_STATES.PENDING.value)


@receiver(post_save, sender=UserProfile, dispatch_uid='custom_user_profile_validation')
def custom_user_profile_validation(sender, instance, **kwargs):
    user_verifications = UserVerification.objects.exclude(state=VERIFICATION_STATES.CLAIMED.value).filter(first_name__iexact=instance.first_name, last_name__iexact=instance.last_name,
                                                                                                          address_street__iexact=instance.address_street, address_town__iexact=instance.address_town,
                                                                                                          address_postal_code=instance.address_postal_code, date_of_birth=instance.date_of_birth, places_of_origin__place_of_origin=instance.place_of_origin)

    if user_verifications.exists():
        user_verification = user_verifications[0]
        user_verification.user_profile = instance
        if instance.owner.user_profiles.filter(user_verification__state=VERIFICATION_STATES.CLAIMED.value).count() >= instance.wallet.currency.max_claims:
            user_verification.state = VERIFICATION_STATES.MAX_CLAIMS.value
            user_verification.save()
        else:
            user_verification.state = VERIFICATION_STATES.PENDING.value

            SMSPinVerification.objects.create(
                user_profile=instance, state=VERIFICATION_STATES.PENDING.value)
            user_verification.save()
