import requests
from django.conf import settings


def accept_verfication_and_create_transaction(obj):
    pass


def send_sms(to_number: str, message: str):
    if not settings.DEBUG:
        send_sms_url = settings.MAILJET_API_URL + 'sms-send'
        response = requests.post(send_sms_url,
                                 headers={
                                     'Authorization': 'Bearer ' + settings.MAILJET_SMS_TOKEN,
                                     'Content-Type': 'application/json'
                                 },
                                 json={
                                     'Text': message,
                                     'To': to_number,
                                     'From': settings.MAILJET_SENDER_ID
                                 })
        # TODO: Check different possible responses and handle outcomes accordingly, e.g. with status

        # return (response.ok, response.text)
    else:
        print('sending immaginary SMS to {}:"{}"'.format(to_number, message))
