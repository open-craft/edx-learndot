"""
Django models required for integration with Learndot
"""

from __future__ import absolute_import, unicode_literals

from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CourseMapping(models.Model):
    """A mapping of edX courses to Learndot components."""
    learndot_component_id = models.BigIntegerField(help_text="The numeric ID of the Learndot component.")
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

class EnrolmentStatusLog(models.Model):
    """A record of an update to a Learndot enrolment."""
    learndot_enrolment_id = models.BigIntegerField(
        primary_key=True,
        help_text="The numeric ID of the Learndot enrolment."
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="The timestamp of the last change to this enrolment.")
    status = models.TextField(
        help_text="The last status sent to Learndot."
    )

    class Meta(object):
        app_label = "edxlearndot"

    def __str__(self):
        return self.__unicode__().encode("utf8")

    def __unicode__(self):
        return "learndot_enrolment_id={}, status={} at {}".format(
            self.learndot_enrolment_id,
            self.status,
            self.updated_at
        )
