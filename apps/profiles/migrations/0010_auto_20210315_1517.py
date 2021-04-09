# Generated by Django 3.1 on 2021-03-15 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0009_auto_20201023_0908"),
    ]

    operations = [
        migrations.AlterField(
            model_name="companyprofile",
            name="address_postal_code",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Postal code"
            ),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="address_street",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Street"
            ),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="address_town",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Town"
            ),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="name",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Name"
            ),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="uid",
            field=models.CharField(
                blank=True, max_length=15, null=True, verbose_name="uid"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="address_postal_code",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Postcode"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="address_street",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Street"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="address_town",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="City"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True, verbose_name="Birthdate"),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Firstname"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="last_name",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Lastname"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="place_of_origin",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="Place of origin"
            ),
        ),
    ]
