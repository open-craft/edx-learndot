# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edxlearndot', '0002_auto_20180319_1550'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnrolmentStatusLog',
            fields=[
                ('learndot_enrolment_id', models.BigIntegerField(help_text='The numeric ID of the Learndot enrolment.', serialize=False, primary_key=True)),
                ('updated_at', models.DateTimeField(help_text='The timestamp of the last change to this enrolment.', auto_now=True)),
                ('status', models.TextField(help_text='The last status sent to Learndot.')),
            ],
        ),
        migrations.AlterField(
            model_name='coursemapping',
            name='learndot_component_id',
            field=models.BigIntegerField(help_text='The numeric ID of the Learndot component.'),
        ),
    ]
