# Generated by Django 2.2.13 on 2020-06-25 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wallet", "0004_auto_20200625_1512"),
    ]

    operations = [
        migrations.AddField(
            model_name="tokentransaction",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="tokentransaction",
            name="submitted_to_chain_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="wallet",
            name="is_owner_wallet",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="wallet",
            name="state",
            field=models.IntegerField(default=0),
        ),
    ]
