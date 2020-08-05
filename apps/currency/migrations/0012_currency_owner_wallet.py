# Generated by Django 2.2.14 on 2020-08-05 08:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0028_auto_20200805_0822'),
        ('currency', '0011_auto_20200722_1403'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='owner_wallet',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='currencies', to='wallet.OwnerWallet'),
        ),
    ]
