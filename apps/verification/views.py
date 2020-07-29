from django.core.exceptions import FieldError, PermissionDenied
from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.verification.models import (VERIFICATION_STATES, CompanyVerification,
                                      UserVerification, VerificationInput)
from apps.verification.serializers import (VerificationInputDataSerializer,
                                           VerificationInputSerializer)
from apps.wallet.models import (WALLET_CATEGORIES, WALLET_STATES,
                                MetaTransaction, Wallet)
from apps.wallet.serializers import WalletSerializer
from apps.wallet.utils import create_claim_transaction
from project.utils import raise_api_exception


class VerificationInputList(generics.ListAPIView):
    serializer_class = VerificationInputSerializer
    filterset_fields = ['currency__uuid', 'used_for_companies']
    queryset = VerificationInput.objects.all()


@api_view(['POST'])
def verify_wallet(request, wallet_id=None):
    wallet = Wallet.objects.get(wallet_id=wallet_id)

    if wallet.owner != request.user:
        raise PermissionDenied("The wallet does not belong to you")

    data = {}

    for verification_input in request.data:
        data[verification_input['label']] = verification_input['value']

    data['currency'] = wallet.currency

    if wallet.category == WALLET_CATEGORIES.COMPANY.value:
        VerificationModel = CompanyVerification
    else:
        VerificationModel = UserVerification
    try:
        obj, created = VerificationModel.objects.get_or_create(**data)
    except FieldError:
        raise_api_exception(
            422, 'Verification could not be done, wrong format of body')
    verification_ok = False

    if created:
        obj.state = VERIFICATION_STATES.REQUESTED.value
        obj.receiving_wallet = wallet
        obj.save()
    elif obj.state == VERIFICATION_STATES.OPEN.value:
        obj.receiving_wallet = wallet

        if wallet.claim_count >= wallet.currency.max_claims:
            obj.state = VERIFICATION_STATES.CLAIM_LIMIT_REACHED.value
            obj.save()
            raise_api_exception(
                403, f'You can not claim more than {wallet.currency.max_claims} times')
        obj.state = VERIFICATION_STATES.CLAIMED.value
        obj.save()
        verification_ok = True

    else:
        if obj.receiving_wallet == wallet:
            raise_api_exception(
                403, 'You can not request or claim twice with the same data')

        obj_new = VerificationModel.objects.create(**data)
        obj_new.state = VERIFICATION_STATES.DOUBLE_CLAIM.value
        obj_new.receiving_wallet = wallet
        obj_new.save()

    if verification_ok:
        wallet.state = WALLET_STATES.VERIFIED.value
        wallet.save()
        
        if wallet.category == WALLET_CATEGORIES.CONSUMER.value:
            create_claim_transaction(wallet)

    else:
        raise_api_exception(406, 'Verification could not be done')

    return Response(WalletSerializer(wallet).data)


@api_view(['GET'])
def get_verification_input(request, currency_uuid=None):
    for_company = request.query_params.get('used_for_companies', False)

    if for_company:
        return Response(CompanyVerification.to_verification_input_dict())
    else:
        return Response(UserVerification.to_verification_input_dict())
