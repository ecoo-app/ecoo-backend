# Generated by Django 2.2.14 on 2020-07-17 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wallet", "0014_auto_20200717_0945"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wallet",
            name="pub_key",
            field=models.CharField(max_length=60, unique=True),
        ),
    ]
