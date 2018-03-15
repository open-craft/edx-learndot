"""
Test the models supporting Learndot integration.
"""

from __future__ import absolute_import, unicode_literals

from django.db import IntegrityError
from django.test import TestCase

from opaque_keys.edx.keys import CourseKey

from edxlearndot.models import CourseMapping


class CourseMappingTestCase(TestCase):
    """
    Test the CourseMapping model.
    """
    def setUp(self):
        self.course1_key = CourseKey.from_string("course-v1:Test+TestCourse+201801")
        self.course2_key = CourseKey.from_string("course-v1:Test+TestCourse+201802")

    def test_only_one_course_is_permitted_per_component(self):
        with self.assertRaises(IntegrityError):
            CourseMapping.objects.create(learndot_component_id=1, edx_course_key=self.course1_key)
            CourseMapping.objects.create(learndot_component_id=1, edx_course_key=self.course2_key)

    def test_multiple_components_per_course_is_ok(self):
        CourseMapping.objects.create(learndot_component_id=1, edx_course_key=self.course1_key)
        CourseMapping.objects.create(learndot_component_id=2, edx_course_key=self.course1_key)
        self.assertEqual(CourseMapping.objects.filter(edx_course_key=self.course1_key).count(), 2)
