# Generated by Django 3.1 on 2020-09-10 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0006_companyprofile_phone_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="companyprofile",
            name="address_postal_code",
            field=models.CharField(max_length=128, verbose_name="Postal code"),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="address_street",
            field=models.CharField(max_length=128, verbose_name="Street"),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="address_town",
            field=models.CharField(max_length=128, verbose_name="Town"),
        ),
    ]
