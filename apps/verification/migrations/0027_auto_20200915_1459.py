# Generated by Django 3.1 on 2020-09-15 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0026_auto_20200915_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companyverification',
            name='address_postal_code',
            field=models.CharField(max_length=128, verbose_name='Postleitzahl'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='address_street',
            field=models.CharField(max_length=128, verbose_name='Strasse'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='address_town',
            field=models.CharField(max_length=128, verbose_name='Stadt'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='uid',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Uid'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='address_postal_code',
            field=models.CharField(max_length=128, null=True, verbose_name='Postleitzahl'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='address_street',
            field=models.CharField(max_length=128, null=True, verbose_name='Strasse'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='address_town',
            field=models.CharField(max_length=128, null=True, verbose_name='Stadt'),
        ),
    ]
