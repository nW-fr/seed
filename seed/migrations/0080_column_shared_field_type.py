# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-06 02:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seed', '0079_propertystate_ubid'),
    ]

    operations = [
        migrations.AddField(
            model_name='column',
            name='shared_field_type',
            field=models.IntegerField(choices=[(0, b'None'), (1, b'Public')], default=0),
        ),
    ]
