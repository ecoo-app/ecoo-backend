from django.conf import settings
from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from urllib.parse import urlencode


@api_view()
@permission_classes([AllowAny])
def version(request):
    return Response({"version": 2})

@api_view()
@permission_classes([AllowAny])
def deeplink(request):
    hotfix_link = "https://ecoo.page.link/?"
            + urlencode(
                {
                    "link": "{}wallet/?{}".format(
                        settings.DEEPLINK_BASE_URL, request.GET.urlencode()
                    )
                }
            )
            + "&apn=ch.ecoupon.mobile.android&ibi=ch.ecoupon.mobile&isi="
            + settings.DEEPLINK_ISI_PARAM
    return redirect(hotfix_link)
