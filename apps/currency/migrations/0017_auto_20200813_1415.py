# Generated by Django 3.1 on 2020-08-13 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0016_auto_20200812_2338'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='currency',
            options={'verbose_name': 'Currency', 'verbose_name_plural': 'Currencies'},
        ),
        migrations.AlterField(
            model_name='currency',
            name='allow_minting',
            field=models.BooleanField(default=True, verbose_name='Allow minting'),
        ),
        migrations.AlterField(
            model_name='currency',
            name='campaign_end',
            field=models.DateField(null=True, verbose_name='Campaign end'),
        ),
        migrations.AlterField(
            model_name='currency',
            name='claim_deadline',
            field=models.DateField(null=True, verbose_name='Claim deadline'),
        ),
        migrations.AlterField(
            model_name='currency',
            name='decimals',
            field=models.IntegerField(default=0, verbose_name='Decimals'),
        ),
        migrations.AlterField(
            model_name='currency',
            name='max_claims',
            field=models.IntegerField(default=5, verbose_name='Max claims'),
        ),
        migrations.AlterField(
            model_name='currency',
            name='starting_capital',
            field=models.IntegerField(default=10, verbose_name='Starting capital'),
        ),
        migrations.AlterField(
            model_name='currency',
            name='token_id',
            field=models.IntegerField(verbose_name='Token Id'),
        ),
    ]
