# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('learndot_component_id', models.IntegerField(help_text=b'The numeric ID of the Learndot component.', unique=True)),
                ('edx_course_key', opaque_keys.edx.django.models.CourseKeyField(help_text=b'The edX course ID.', max_length=255, db_index=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='coursemapping',
            unique_together=set([('learndot_component_id', 'edx_course_key')]),
        ),
    ]
