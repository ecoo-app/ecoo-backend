from rest_framework.exceptions import APIException


def raise_api_exception(code, msg):
    e = APIException()
    e.status_code = code
    e.detail = msg
    raise e
