# Generated by Django 2.2.14 on 2020-07-20 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0006_auto_20200716_1354'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='allow_minting',
            field=models.BooleanField(default=True),
        ),
    ]
