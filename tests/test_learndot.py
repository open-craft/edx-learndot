"""
Test the Learndot API
"""

from __future__ import absolute_import, unicode_literals

import unittest

from edxlearndot.learndot import EnrolmentStatus, compare_enrolment_sort_keys, sort_enrolments_by_expiry


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

    def test_validity_check(self):
        self.assertTrue(EnrolmentStatus.is_valid("PASSED"))
        self.assertFalse(EnrolmentStatus.is_valid("BUNGLED"))
