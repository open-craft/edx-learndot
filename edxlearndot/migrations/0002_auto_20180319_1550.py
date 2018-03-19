# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edxlearndot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursemapping',
            name='learndot_component_id',
            field=models.IntegerField(help_text='The numeric ID of the Learndot component.'),
        ),
    ]
