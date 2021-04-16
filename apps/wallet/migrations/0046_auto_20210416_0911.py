# Generated by Django 3.1 on 2021-04-16 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wallet", "0045_auto_20210308_0751"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="user_notes",
            field=models.TextField(blank=True, verbose_name="User notes"),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Notes"),
        ),
    ]
