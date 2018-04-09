"""
Signal handling required for Learndot integration
"""


from __future__ import absolute_import, unicode_literals

import logging

from edxlearndot.learndot import LearndotAPIClient
from edxlearndot.models import CourseMapping


log = logging.getLogger(__name__)


def listen_for_passing_grade(sender, user, course_id, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for a learner passing a course.

    When this happens, use the LearnDot API to complete the user's
    latest valid enrolment.

    Arguments:
        user (`django.contrib.auth.models.User`): the edX learner's user object
        course_id (`opaque_keys.edx.locator.CourseLocator`): the ID of the edX course that's been passed

    Returns:
        None

    """

    log.info("Updating Learndot enrolment for new passing grade: user=%s, course=%s", user, course_id)

    learndot_client = LearndotAPIClient()
    contact_id = learndot_client.get_contact_id(user)

    if contact_id and course_id:
        course_mappings = CourseMapping.objects.filter(edx_course_key=course_id)
        for cm in course_mappings:
            learndot_client.check_if_enrolment_and_set_status_to_passed(contact_id, cm.learndot_component_id)
