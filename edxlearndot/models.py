"""
Django models required for integration with Learndot
"""

from __future__ import absolute_import, unicode_literals

from django.db import models

from opaque_keys.edx.django.models import CourseKeyField


class CourseMapping(models.Model):
    """A mapping of edX courses to Learndot components."""
    learndot_component_id = models.IntegerField(help_text="The numeric ID of the Learndot component.")
    edx_course_key = CourseKeyField(max_length=255, db_index=True, help_text="The edX course ID.")

    class Meta(object):
        app_label = "edxlearndot"
        unique_together = ("learndot_component_id", "edx_course_key")

    def __str__(self):
        return self.__unicode__().encode("utf8")

    def __unicode__(self):
        return "learndot_component_id={}, edx_course_key={}".format(
            self.learndot_component_id,
            self.edx_course_key
        )
