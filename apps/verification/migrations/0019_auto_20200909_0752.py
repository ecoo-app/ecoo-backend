# Generated by Django 3.1 on 2020-09-09 07:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0018_placeoforigin'),
    ]

    operations = [
        migrations.RenameField(
            model_name='placeoforigin',
            old_name='place_of_origint',
            new_name='place_of_origin',
        ),
    ]
