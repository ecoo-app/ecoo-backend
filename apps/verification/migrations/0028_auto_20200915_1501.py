# Generated by Django 3.1 on 2020-09-15 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0027_auto_20200915_1459"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userverification",
            name="address_postal_code",
            field=models.CharField(max_length=128, verbose_name="Postleitzahl"),
        ),
        migrations.AlterField(
            model_name="userverification",
            name="address_street",
            field=models.CharField(max_length=128, verbose_name="Strasse"),
        ),
        migrations.AlterField(
            model_name="userverification",
            name="address_town",
            field=models.CharField(max_length=128, verbose_name="Stadt"),
        ),
    ]
