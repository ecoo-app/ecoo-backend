from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.profiles.models import UserProfile, CompanyProfile
from apps.verification.models import SMSPinVerification, VERIFICATION_STATES
from apps.wallet.models import WALLET_CATEGORIES, WALLET_STATES
from apps.wallet.utils import create_claim_transaction
from project.utils import raise_api_exception
from apps.verification.utils import send_sms


@api_view(['POST'])
def resend_user_profile_pin(request, user_profile_uuid=None):
    user_profile = UserProfile.objects.get(uuid=user_profile_uuid)
    if user_profile.owner != request.user:
        raise PermissionDenied("The profile does not belong to you")
    if user_profile.sms_pin_verification.state == VERIFICATION_STATES.PENDING.value:
        send_sms(user_profile.telephone_number,
                 user_profile.sms_pin_verification.pin)
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        raise_api_exception(
            422, 'no pin verification open for given user profile at this time')


@api_view(['POST'])
def verify_user_profile_pin(request, user_profile_uuid=None):
    user_profile = UserProfile.objects.get(uuid=user_profile_uuid)
    if user_profile.owner != request.user:
        raise PermissionDenied("The profile does not belong to you")

    if user_profile.sms_pin_verification.state == VERIFICATION_STATES.PENDING.value and user_profile.sms_pin_verification.pin == request.data.get('pin', 'XX'):
        if request.user.wallets.filter(category=WALLET_CATEGORIES.CONSUMER.value, wallet_id=request.data.get('wallet_id', 'XX')).exists():
            user_profile.sms_pin_verification.state = VERIFICATION_STATES.CLAIMED.value
            user_profile.sms_pin_verification.save()
            user_profile.user_verification.state = VERIFICATION_STATES.CLAIMED.value
            user_profile.user_verification.save()
            wallet = request.user.wallets.get(
                category=WALLET_CATEGORIES.CONSUMER.value, wallet_id=request.data.get('wallet_id', 'XX'))
            wallet.state = WALLET_STATES.VERIFIED.value
            wallet.save()
            create_claim_transaction(wallet)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise_api_exception(
                status.HTTP_404_NOT_FOUND, 'wallet matching wallet_id not found among the wallets you own')
    else:
        user_profile.sms_pin_verification.delete()
        SMSPinVerification.objects.create(
            user_profile=user_profile, state=VERIFICATION_STATES.PENDING.value)
        raise_api_exception(
            422, 'PIN did not match, we resent a new one')


@api_view(['POST'])
def verify_company_profile_pin(request, company_profile_uuid=None):
    company_profile = CompanyProfile.objects.get(uuid=company_profile_uuid)
    if company_profile.owner != request.user:
        raise PermissionDenied("The profile does not belong to you")

    if company_profile.address_pin_verification.state == VERIFICATION_STATES.PENDING.value and company_profile.address_pin_verification.pin == request.data.get('pin', 'XX'):
        if request.user.wallets.filter(category=WALLET_CATEGORIES.COMPANY.value, wallet_id=request.data.get('wallet_id', 'XX')).exists():
            company_profile.address_pin_verification.state = VERIFICATION_STATES.CLAIMED.value
            company_profile.address_pin_verification.save()
            company_profile.company_verification.state = VERIFICATION_STATES.CLAIMED.value
            company_profile.company_verification.save()
            wallet = request.user.wallets.get(
                category=WALLET_CATEGORIES.COMPANY.value, wallet_id=request.data.get('wallet_id', 'XX'))
            wallet.state = WALLET_STATES.VERIFIED.value
            wallet.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise_api_exception(
                status.HTTP_404_NOT_FOUND, 'wallet matching wallet_id not found among the wallets you own')
    else:
        raise_api_exception(
            422, 'PIN did not match')
