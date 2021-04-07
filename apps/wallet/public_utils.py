import csv
import os
import uuid
import zipfile

import pyqrcode
import pytezos
from django.conf import settings
from django.db import IntegrityError
from PIL import Image


def generate_paper_wallet(currency, category):
    from apps.wallet.models import PaperWallet

    key = pytezos.crypto.key.Key.generate()
    private_key = key.secret_key()
    public_key = key.public_key()

    retry = True
    while retry:
        try:
            paper_wallet = PaperWallet.objects.create(
                currency=currency,
                private_key=private_key,
                wallet_id=PaperWallet.generate_wallet_id(),
                public_key=public_key,
                category=category,
            )
            retry = False
        except IntegrityError:
            retry = True
    return paper_wallet


def generate_qr_code_zip(queryset, add_wallet_id_csv=False):

    zip_filename = os.path.join(
        settings.MEDIA_ROOT, "zip", "qr_codes_{}.zip".format(uuid.uuid4())
    )

    with zipfile.ZipFile(zip_filename, "w") as zf:
        for wallet in queryset:

            qr_code = pyqrcode.create(wallet.generate_deeplink(), error="M")
            filename = os.path.join(
                settings.MEDIA_ROOT, "qr", wallet.wallet_id + ".png"
            )
            qr_code.png(filename, scale=5)
            img = Image.open(filename)

            img = img.resize((530, 530), Image.ANTIALIAS)
            img.save(filename)

            zf.write(filename)

        if add_wallet_id_csv:
            csv_name = os.path.join(
                settings.MEDIA_ROOT, "zip", "wallet_ids_{}.csv".format(uuid.uuid4())
            )
            with open(csv_name, "w", newline="") as csvfile:
                writer = csv.writer(
                    csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
                )
                for wallet in queryset:
                    writer.writerow([wallet.wallet_id])

            zf.write(csv_name)
    return zip_filename
