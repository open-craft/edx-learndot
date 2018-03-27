"""
Test the Learndot API
"""

from __future__ import absolute_import, unicode_literals

import unittest

from edxlearndot.learndot import (
    EnrolmentStatus, LearndotAPIClientMock, LearndotAPIException,
    compare_enrolment_sort_keys, sort_enrolments_by_expiry
)
from edxlearndot.models import EnrolmentStatusLog


class TestEnrolmentSorting(unittest.TestCase):
    """
    Test that lists of enrolments in API results can be sorted properly.
    """

    def test_enrolment_expiry_comparator(self):
        t1 = ("2018-01-01", "2018-02-01")
        t2 = ("2018-01-01", "2018-02-01", "2018-02-03")

        self.assertEqual(1, compare_enrolment_sort_keys(t1, t2))

        t1 = ("2018-01-01", "2018-02-01")
        t2 = ("2018-01-01", "2018-02-01")

        self.assertEqual(0, compare_enrolment_sort_keys(t1, t2))

        t1 = ("2018-01-01", "2018-02-01", "2018-03-01")
        t2 = ("2018-01-01", "2018-02-01")

        self.assertEqual(-1, compare_enrolment_sort_keys(t1, t2))

    def test_enrolments_with_expiry(self):
        enrolment_list = [
            {
                "componentId": 1,
                "contactId": 1,
                "expiryDate": "2018-01-31 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "2018-01-01 00:00:00",
            },
            {
                "componentId": 1,
                "contactId": 2,
                "expiryDate": "2018-01-10 00:00:00",
            },
        ]

        properly_sorted_enrolment_list = [
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "2018-01-01 00:00:00",
            },
            {
                "componentId": 1,
                "contactId": 2,
                "expiryDate": "2018-01-10 00:00:00",
            },
            {
                "componentId": 1,
                "contactId": 1,
                "expiryDate": "2018-01-31 00:00:00",
            },
        ]

        self.assertEqual(sort_enrolments_by_expiry(enrolment_list), properly_sorted_enrolment_list)


    def test_sort_missing_expiry(self):
        """
        Test sorting of enrolments missing expiryDates.

        Enrolments with expiryDates should be first.
        """
        enrolment_list = [
            {
                "componentId": 1,
                "contactId": 1,
            },
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "",
            },
            {
                "componentId": 3,
                "contactId": 1,
                "expiryDate": None,
            },
            {
                "componentId": 2,
                "contactId": 1,
                "created": "2018-02-01 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "modified": "2018-01-02 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "created": "2018-01-01 00:00:00",
                "modified": "2018-02-02 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "2018-03-01 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "2018-01-01 00:00:00",
            },
        ]

        properly_sorted_enrolment_list = [
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "2018-01-01 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "2018-03-01 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "modified": "2018-01-02 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "created": "2018-02-01 00:00:00",
            },
            {
                "componentId": 2,
                "contactId": 1,
                "created": "2018-01-01 00:00:00",
                "modified": "2018-02-02 00:00:00",
            },
            {
                "componentId": 1,
                "contactId": 1,
            },
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "",
            },
            {
                "componentId": 3,
                "contactId": 1,
                "expiryDate": None,
            },
        ]

        self.maxDiff = None
        self.assertEqual(sort_enrolments_by_expiry(enrolment_list), properly_sorted_enrolment_list)

    def test_sort_bad_expiry_format(self):
        enrolment_list = [
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "HA! NO",
            },
            {
                "componentId": 1,
                "contactId": 2,
                "expiryDate": "2018-01-10 00:00:00",
            },
        ]

        with self.assertRaises(ValueError):
            sort_enrolments_by_expiry(enrolment_list)

    def test_sort_ridiculous_expiry_date(self):
        enrolment_list = [
            {
                "componentId": 2,
                "contactId": 1,
                "expiryDate": "99999999999999999999-01-01 00:00:00",
            },
            {
                "componentId": 1,
                "contactId": 2,
                "expiryDate": "2018-01-10 00:00:00",
            },
        ]

        with self.assertRaises(OverflowError):
            sort_enrolments_by_expiry(enrolment_list)


class TestEnrolmentStatus(unittest.TestCase):
    """
    Test for valid values in edxlearndot.learndot.EnrolmentStatus.
    """
    def test_validity_check(self):
        self.assertTrue(EnrolmentStatus.is_valid("PASSED"))
        self.assertFalse(EnrolmentStatus.is_valid("BUNGLED"))


class TestLearndot(unittest.TestCase):
    """
    Test edxlearndot.learndot.

    Without actually talking to a Learndot sandbox, we're limited in
    what we can test, but we can use a mock client to check tangents
    like the EnrolmentStatusLog recording.
    """

    def test_set_enrolment_status_success_is_logged(self):
        """
        Test that a successful update is logged locally.
        """
        client = LearndotAPIClientMock()

        client.set_enrolment_status(2, "PASSED")
        self.assertEqual(EnrolmentStatusLog.objects.filter(learndot_enrolment_id=2).count(), 1)

    def test_set_enrolment_status_failure_is_not_logged(self):
        """
        Test that a failed update creates no local status log records.
        """
        client = LearndotAPIClientMock()

        with self.assertRaises(LearndotAPIException):
            client.set_enrolment_status(client.DOES_NOT_EXIST_ID, "PASSED")
        self.assertEqual(EnrolmentStatusLog.objects.filter(learndot_enrolment_id=1).count(), 0)
