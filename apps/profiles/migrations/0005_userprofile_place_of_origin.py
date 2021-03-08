# Generated by Django 3.1 on 2020-09-09 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0004_auto_20200826_1340"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="place_of_origin",
            field=models.CharField(
                default="", max_length=128, verbose_name="Place of origin"
            ),
            preserve_default=False,
        ),
    ]
