# Generated by Django 2.2.13 on 2020-07-20 07:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0015_auto_20200717_1002'),
    ]

    operations = [
        migrations.RenameField(
            model_name='wallet',
            old_name='wallet_type',
            new_name='category',
        ),
        migrations.RenameField(
            model_name='wallet',
            old_name='pub_key',
            new_name='public_key',
        ),
        migrations.RenameField(
            model_name='wallet',
            old_name='walletID',
            new_name='wallet_id',
        ),
    ]
