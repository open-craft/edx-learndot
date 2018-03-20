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

    def test_many_to_many_mapping(self):
        """
        You can have more than one Learndot component per edX course, and
        vice versa, but only one mapping for any pair.
        """
        CourseMapping.objects.create(learndot_component_id=1, edx_course_key=self.course1_key)
        CourseMapping.objects.create(learndot_component_id=1, edx_course_key=self.course2_key)
        CourseMapping.objects.create(learndot_component_id=2, edx_course_key=self.course1_key)
        CourseMapping.objects.create(learndot_component_id=2, edx_course_key=self.course2_key)

        self.assertEqual(CourseMapping.objects.count(), 4)
        self.assertEqual(CourseMapping.objects.filter(edx_course_key=self.course1_key).count(), 2)
        self.assertEqual(CourseMapping.objects.filter(edx_course_key=self.course2_key).count(), 2)

        with self.assertRaises(IntegrityError):
            CourseMapping.objects.create(learndot_component_id=1, edx_course_key=self.course1_key)
