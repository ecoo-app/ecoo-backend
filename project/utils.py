from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.pagination import CursorPagination
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer

def raise_api_exception(code, msg):
    e = APIException()
    e.status_code = code
    e.detail = msg
    raise e


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        return response
    elif isinstance(exc, ValidationError):
        return Response({'detail': exc.messages}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    else:
        return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomCursorPagination(CursorPagination):
    ordering = 'created_at'
    page_size = 10
    page_size_query_param = 'page_size'


class CustomJsonRenderer(JSONRenderer):
    charset = 'utf-8'
