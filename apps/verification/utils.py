import json

import requests
from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


def accept_verfication_and_create_transaction(obj):
    pass


def send_sms(to_number: str, message: str):
    if settings.ENABLE_SMS:
        send_sms_url = settings.MAILJET_API_URL + "sms-send"
        response = requests.post(
            send_sms_url,
            headers={
                "Authorization": "Bearer " + settings.MAILJET_SMS_TOKEN,
                "Content-Type": "application/json",
            },
            json={"Text": message, "To": to_number, "From": settings.MAILJET_SENDER_ID},
        )
        # TODO: Check different possible responses and handle outcomes accordingly, e.g. with status
        return (response.ok, response.text)
    else:
        print('sending immaginary SMS to {}:"{}"'.format(to_number, message))


def send_postcard(
    message="",
    firstname=" ",
    lastname=" ",
    company="",
    street="",
    house_nr="",
    zip="",
    city="",
    country="Switzerland",
    po_box="",
    additional_address_info="",
):
    if settings.ENABLE_POSTCARD:
        POST_API_CONFIG = settings.POST_API_CONFIG
        client = BackendApplicationClient(
            client_id=POST_API_CONFIG["client_id"], scope=POST_API_CONFIG["scope"]
        )
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url=POST_API_CONFIG["token_url"],
            client_id=POST_API_CONFIG["client_id"],
            client_secret=POST_API_CONFIG["client_secret"],
        )

        url = (
            POST_API_CONFIG["base_url"]
            + "v1/postcards?campaignKey="
            + POST_API_CONFIG["campaign_key"]
        )
        post_card_creation_response = requests.post(
            url,
            headers={
                "Authorization": token["token_type"] + " " + token["access_token"]
            },
            json={
                "senderAddress": POST_API_CONFIG["sender"],
                "recipientAddress": {
                    "firstname": firstname,
                    "lastname": lastname,
                    "company": company,
                    "street": street,
                    "houseNr": house_nr,
                    "zip": zip,
                    "city": city,
                    "country": country,
                    "poBox": po_box,
                    "additionalAdrInfo": additional_address_info,
                },
                "senderText": message,
                "branding": POST_API_CONFIG["branding"],
            },
        )

        post_card_key = post_card_creation_response.json()["cardKey"]
        post_card_stamp_image = open("static/post_card_stamp.png", "rb")
        stamp_set_url = POST_API_CONFIG[
            "base_url"
        ] + "v1/postcards/{}/branding/stamp".format(post_card_key)
        requests.put(
            stamp_set_url,
            headers={
                "Authorization": token["token_type"] + " " + token["access_token"]
            },
            files={"stamp": post_card_stamp_image},
        )

        post_card_front_image = open("static/post_card_front.jpeg", "rb")
        image_set_url = POST_API_CONFIG["base_url"] + "v1/postcards/{}/image".format(
            post_card_key
        )
        requests.put(
            image_set_url,
            headers={
                "Authorization": token["token_type"] + " " + token["access_token"]
            },
            files={"image": post_card_front_image},
        )

        approval_url = POST_API_CONFIG["base_url"] + "v1/postcards/{}/approval".format(
            post_card_key
        )

        approval_response = requests.post(
            approval_url,
            headers={
                "Authorization": token["token_type"] + " " + token["access_token"]
            },
        )

        if (
            approval_response.status_code == 200
            and "successMessage" in approval_response.json()
        ):
            return (approval_response.ok, post_card_key)
        else:
            return (False, approval_response.text)
    else:
        print('sending immaginary POSTCARD to {}:"{}"'.format(company, message))
        return (True, "dummy")
