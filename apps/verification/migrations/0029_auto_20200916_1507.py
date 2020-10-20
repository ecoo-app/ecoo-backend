# Generated by Django 3.1 on 2020-09-16 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0028_auto_20200915_1501'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='addresspinverification',
            options={'verbose_name': 'Address pin verification', 'verbose_name_plural': 'Address pin verifications'},
        ),
        migrations.AlterModelOptions(
            name='companyverification',
            options={'verbose_name': 'Company verification', 'verbose_name_plural': 'Company verifications'},
        ),
        migrations.AlterModelOptions(
            name='smspinverification',
            options={'verbose_name': 'SMS pin verification', 'verbose_name_plural': 'SMS pin verifications'},
        ),
        migrations.AlterModelOptions(
            name='userverification',
            options={'verbose_name': 'User verification', 'verbose_name_plural': 'User verifications'},
        ),
        migrations.AlterField(
            model_name='addresspinverification',
            name='state',
            field=models.IntegerField(choices=[(1, 'Open'), (2, 'Pending'), (3, 'Claimed'), (5, 'Failed'), (6, 'Max Claims')], default=1, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='address_postal_code',
            field=models.CharField(max_length=128, verbose_name='Postal code'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='address_street',
            field=models.CharField(max_length=128, verbose_name='Street'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='address_town',
            field=models.CharField(max_length=128, verbose_name='Town'),
        ),
        migrations.AlterField(
            model_name='companyverification',
            name='state',
            field=models.IntegerField(choices=[(1, 'Open'), (2, 'Pending'), (3, 'Claimed'), (5, 'Failed'), (6, 'Max Claims')], default=1, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='smspinverification',
            name='state',
            field=models.IntegerField(choices=[(1, 'Open'), (2, 'Pending'), (3, 'Claimed'), (5, 'Failed'), (6, 'Max Claims')], default=1, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='address_postal_code',
            field=models.CharField(max_length=128, verbose_name='Postal code'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='address_street',
            field=models.CharField(max_length=128, verbose_name='Street'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='address_town',
            field=models.CharField(max_length=128, verbose_name='Town'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='date_of_birth',
            field=models.DateField(verbose_name='Date of birth'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='first_name',
            field=models.CharField(max_length=128, verbose_name='Firstname'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='last_name',
            field=models.CharField(max_length=128, verbose_name='Lastname'),
        ),
        migrations.AlterField(
            model_name='userverification',
            name='state',
            field=models.IntegerField(choices=[(1, 'Open'), (2, 'Pending'), (3, 'Claimed'), (5, 'Failed'), (6, 'Max Claims')], default=1, verbose_name='State'),
        ),
    ]
