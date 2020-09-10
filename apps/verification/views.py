from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect

from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.currency.models import Currency
from apps.profiles.models import CompanyProfile, UserProfile
from apps.verification.models import (VERIFICATION_STATES, CompanyVerification,
                                      SMSPinVerification, UserVerification, AddressPinVerification)

from apps.verification.serializers import (AutocompleteCompanySerializer,
                                           AutocompleteUserSerializer)
from apps.verification.utils import send_sms
from apps.wallet.models import WALLET_CATEGORIES, WALLET_STATES, PaperWallet
from apps.wallet.utils import create_claim_transaction
from project.utils import raise_api_exception

from django.db.models import Q
from django.views.generic.detail import DetailView


class AddressPinVerificationView(DetailView):
    model = AddressPinVerification


@api_view(['POST'])
def resend_user_profile_pin(request, user_profile_uuid=None):
    user_profile = UserProfile.objects.get(uuid=user_profile_uuid)
    if user_profile.owner != request.user:
        raise PermissionDenied(_("The profile does not belong to you"))
    if user_profile.sms_pin_verification != None and user_profile.sms_pin_verification.state == VERIFICATION_STATES.PENDING.value:
        send_sms(user_profile.telephone_number,
                 user_profile.sms_pin_verification.pin)
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        raise_api_exception(
            422, _('There is no pin verification open for the given user profile at this time'))


@api_view(['POST'])
def verify_user_profile_pin(request, user_profile_uuid=None):
    user_profile = UserProfile.objects.get(uuid=user_profile_uuid)
    if user_profile.owner != request.user:
        raise PermissionDenied(_("The profile does not belong to you"))

    if user_profile.sms_pin_verification != None and user_profile.sms_pin_verification.state == VERIFICATION_STATES.PENDING.value and user_profile.sms_pin_verification.pin == request.data.get('pin', 'XX'):
        user_profile.sms_pin_verifications.filter(
            state=VERIFICATION_STATES.PENDING.value).update(state=VERIFICATION_STATES.CLAIMED.value)
        # does this fail if multiple profiles are created?
        user_profile.user_verification.state = VERIFICATION_STATES.CLAIMED.value
        user_profile.user_verification.save()
        user_profile.wallet.state = WALLET_STATES.VERIFIED.value
        user_profile.wallet.save()
        create_claim_transaction(user_profile.wallet)
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        user_profile.sms_pin_verifications.filter(
            state=VERIFICATION_STATES.PENDING.value).update(state=VERIFICATION_STATES.FAILED.value)
        SMSPinVerification.objects.create(
            user_profile=user_profile, state=VERIFICATION_STATES.PENDING.value)
        raise_api_exception(
            422, _('PIN did not match, we resent a new one'))


@api_view(['POST'])
def verify_company_profile_pin(request, company_profile_uuid=None):
    company_profile = CompanyProfile.objects.get(uuid=company_profile_uuid)
    if company_profile.owner != request.user:
        raise PermissionDenied(_("The profile does not belong to you"))

    if company_profile.address_pin_verification.state == VERIFICATION_STATES.PENDING.value and company_profile.address_pin_verification.pin == request.data.get('pin', 'XX'):
        company_profile.address_pin_verification.state = VERIFICATION_STATES.CLAIMED.value
        company_profile.address_pin_verification.save()
        company_profile.company_verification.state = VERIFICATION_STATES.CLAIMED.value
        company_profile.company_verification.save()
        company_profile.wallet.state = WALLET_STATES.VERIFIED.value
        company_profile.wallet.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        raise_api_exception(
            422, _('PIN did not match'))


class AutocompleteUserList(generics.ListAPIView):
    serializer_class = AutocompleteUserSerializer

    def list(self, request):
        self.request = request
        return super(AutocompleteUserList, self).list(request)

    def get_queryset(self):
        search_string = self.request.query_params.get('search', '')
        if search_string.strip() == '':
            return UserVerification.objects.none()

        qs = UserVerification.objects.filter(
            Q(address_street__istartswith=search_string)).distinct('address_street', 'address_town', 'address_postal_code')
        pks = qs.values_list('uuid', flat=True)
        return UserVerification.objects.filter(uuid__in=pks)


class AutocompleteCompanyList(generics.ListAPIView):
    serializer_class = AutocompleteCompanySerializer

    def list(self, request):
        self.request = request
        return super(AutocompleteCompanyList, self).list(request)

    def get_queryset(self):
        search_string = self.request.GET['search']
        if search_string.strip() == '':
            return CompanyVerification.objects.none()
        qs = CompanyVerification.objects.filter(
            Q(address_street__istartswith=search_string)).distinct('address_street','address_town', 'address_postal_code')
        pks = qs.values_list('uuid', flat=True)
        return CompanyVerification.objects.filter(uuid__in=pks)


@staff_member_required
def create_paper_wallet_from_userverification(request, uuid):
    user_verification = UserVerification.objects.get(uuid=uuid)
    if user_verification.state != VERIFICATION_STATES.OPEN.value:
        return redirect('admin:verification_userverification_changelist')

    paper_wallet = PaperWallet.generate_new_wallet(
        currency=Currency.objects.all().first(), verification_data=user_verification)
    create_claim_transaction(paper_wallet)
    user_verification = UserVerification.objects.get(uuid=uuid)
    user_verification.state = VERIFICATION_STATES.CLAIMED.value
    user_verification.save()

    return redirect('admin:wallet_paperwallet_change', paper_wallet.uuid)
