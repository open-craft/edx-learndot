#!/usr/bin/env python

"""
Django management command to update Learndot enrolments.
"""

from __future__ import absolute_import, unicode_literals

import logging
import sys

from django.core.management.base import BaseCommand

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.courses import get_course
from lms.djangoapps.grades.config import should_persist_grades
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from student.models import CourseEnrollment

from edxlearndot.learndot import LearndotAPIClient
from edxlearndot.models import CourseMapping


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to update Learndot enrolments from edX grades
    """
    help = """Update Learndot enrolments based on grades in edX courses"""
    args = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "-u",
            "--username",
            action="append",
            dest="users",
            metavar="user",
            default=[],
            help=("""If usernames are given, only update enrollments for those users.""")
        )

        parser.add_argument(
            "-f",
            "--force",
            dest="unconditional",
            action="store_true",
            default=False,
            help=(
                """Skip the usual attempt to avoid API calls for enrolments that have already been updated, and """
                """just send Learndot all current enrolment status information."""
            )
        )

        parser.add_argument(
            "course_id",
            nargs="*",
            help=("""If course IDs are given, only update enrollments for those courses.""")
        )

    def handle(self, *args, **options):

        # build a list of CourseKeys from any course IDs given
        course_key_list = []
        for course_id in options["course_id"]:
            try:
                course_key_list.append(CourseKey.from_string(course_id))
            except (InvalidKeyError, ValueError):
                log.error("Invalid course ID: %s", course_id)
                sys.exit(1)

        # get the Learndot:edX course mappings
        course_mappings = CourseMapping.objects.all()
        if course_key_list:
            course_mappings = course_mappings.filter(edx_course_key__in=course_key_list)

        if not course_mappings.exists():
            if options["course_id"]:
                log.error("No course mappings were found for your specified course IDs.")
            else:
                log.error("No course mappings were found.")
            sys.exit(1)

        learndot_client = LearndotAPIClient()

        # for each mapped course, go through its enrollments, get the
        # course grade for each enrolled user, and if the user has passed,
        # update the Learndot enrolment
        for cm in course_mappings:
            course = None
            try:
                course = get_course(cm.edx_course_key)
            except (InvalidKeyError, ValueError):
                log.error("Invalid edX course found in map: %s", cm.edx_course_key)
                continue

            log.info("Processing enrollments in course %s", cm.edx_course_key)

            enrollments = CourseEnrollment.objects.filter(course_id=cm.edx_course_key)
            if options["users"]:
                enrollments = enrollments.filter(user__username__in=options["users"])

            for enrollment in enrollments:
                contact_id = learndot_client.get_contact_id(enrollment.user)
                if not contact_id:
                    log.info(
                        "Not setting enrolment status for user %s in course %s, because contact_id is None .",
                        enrollment.user,
                        cm.edx_course_key
                    )
                    continue
                #
                # Disturbingly enough, if persistent grades are not
                # enabled, it just takes looking up the grade to get
                # the Learndot enrolment updated, because when
                # CourseGradeFactory constructs the CourseGrade in its
                # read() method, it will actually call its _update()
                # method, which sends the COURSE_GRADE_NOW_PASSED
                # signal, which of course fires
                # edxlearndot.signals.listen_for_passing_grade.
                #
                # However, if the edX instance has persistent course
                # grades enabled, the CourseGrade doesn't have to be
                # constructed, so the signal isn't fired, and we have
                # to explicitly update Learndot.
                #
                course_grade = CourseGradeFactory().read(enrollment.user, course)
                if not course_grade:
                    log.info(
                        "Not setting enrolment status for user %s in course %s, because no grade is available.",
                        enrollment.user,
                        cm.edx_course_key
                    )
                elif course_grade.passed and should_persist_grades(cm.edx_course_key):
                    log.info("Grades are persistent; explicitly updating Learndot enrolment.")
                    learndot_client.check_if_enrolment_and_set_status_to_passed(
                        contact_id,
                        cm.learndot_component_id,
                        unconditional=options["unconditional"]
                    )
