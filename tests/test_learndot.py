"""
Test the Learndot API
"""

from __future__ import absolute_import, unicode_literals
from mock import patch
import ddt
import requests
import responses
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings

from edxlearndot.learndot import (
    EnrolmentStatus, LearndotAPIClient, LearndotAPIException,
    compare_enrolment_sort_keys, sort_enrolments_by_expiry
)
from edxlearndot.models import EnrolmentStatusLog

from .utils import LearndotAPIClientMock


class TestEnrolmentSorting(TestCase):
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


class TestEnrolmentStatus(TestCase):
    """
    Test for valid values in edxlearndot.learndot.EnrolmentStatus.
    """
    def test_validity_check(self):
        self.assertTrue(EnrolmentStatus.is_valid("PASSED"))
        self.assertFalse(EnrolmentStatus.is_valid("BUNGLED"))


@ddt.ddt
class TestLearndot(TestCase):
    """
    Test edxlearndot.learndot.

    Without actually talking to a Learndot sandbox, we're limited in
    what we can test, but we can use a mock client to check tangents
    like the EnrolmentStatusLog recording.
    """
    def setUp(self):
        self.user = User.objects.create(username="test", email="test@gmail.com", password="test")
        self.client = LearndotAPIClientMock()
        super(TestLearndot, self).setUp()

    def test_get_contact_id(self):
        """
        Test get_contact_id succeeds
        """
        self.assertEqual(self.client.get_contact_id(self.user), 1)

    @patch('edxlearndot.learndot.log')
    def test_get_contact_id_uses_cache(self, mock_logger):
        """
        Test get_contact_id uses cache
        """
        self.client.get_contact_id(self.user)
        mock_logger.info.assert_called_with("Using cached contact ID %s", 1)

    def test_get_api_key(self):
        """
        Test that get_api_key succeeds when LEARNDOT_API_KEY is set
        """
        self.assertEqual(self.client.get_api_key(), 'test')

    def test_get_api_base_url(self):
        """
        Test that API KEY is returned correctly from settings
        """
        self.assertEqual(self.client.get_api_base_url(), 'https://localhost/learndot/v2/api')

    def test_get_enrolment_id(self):
        """
        Test get_enrolment_id succeeds
        """
        self.assertEqual(self.client.get_enrolment_id(1, 2), 1)

    @patch('edxlearndot.learndot.log')
    def test_get_enrolment_id_uses_cache(self, mock_logger):
        self.client.get_enrolment_id(1, 2)
        mock_logger.info.assert_called_with("Using cached enrolment ID %s", 1)

    def test_set_enrolment_status_success_is_logged(self):
        """
        Test that a successful update is logged locally.
        """
        self.client.set_enrolment_status(1, "PASSED")
        self.assertTrue(EnrolmentStatusLog.objects.filter(learndot_enrolment_id=1).exists())

    def test_set_enrolment_status_failure_is_not_logged(self):
        """
        Test that a failed update creates no local status log records.
        """
        with self.assertRaises(LearndotAPIException):
            self.client.set_enrolment_status(2, "INVALID")
        self.assertFalse(EnrolmentStatusLog.objects.filter(learndot_enrolment_id=2).exists())

    def test_check_if_enrolment_and_set_status_to_passed_is_logged(self):
        """
        Test that the update log has status "PASSED".
        """
        self.client.set_enrolment_status(1, "IN_PROGRESS")
        self.client.check_if_enrolment_and_set_status_to_passed(1, 2)
        self.assertEqual(EnrolmentStatusLog.objects.get(learndot_enrolment_id=1).status, "PASSED")


@ddt.ddt
class TestLearndotAPIClient(TestCase):
    """
    Test edxlearndot.learndot API calls.
    """
    def setUp(self):
        super(TestLearndotAPIClient, self).setUp()
        self.user = User.objects.create(username="test", email="test@gmail.com", password="test")
        self.client = LearndotAPIClient()
        responses.start()
        cache.clear()

    def tearDown(self):
        super(TestLearndotAPIClient, self).tearDown()
        responses.stop()
        responses.reset()

    @ddt.data(
        # Retried API errors
        (429, 'Retrying...'),   # Too Many Requests
        (504, 'Retrying...'),   # Gateway Timeout
        (502, 'Retrying...'),   # Rate limit

        # Just error out, no retries
        (400, None),            # Bad Request
        (404, None),            # Not Found
    )
    @ddt.unpack
    @patch('edxlearndot.learndot.log')
    def test_rate_limit_is_retried(self, status_code, retry, mock_logger):
        """
        Test that the rate limit and gateway timeout errors are logged, trigger retries to the API.
        """
        search_url = self.client.get_contact_search_url()
        responses.add(responses.POST,
                      search_url,
                      status=status_code,
        )
        # Ensure the retries eventually max out
        with self.assertRaises(LearndotAPIException):
            self.client.get_contact_id(self.user)

        # And that the request was retried as expected.
        if retry:
            mock_logger.warning.assert_called_with(retry)
        else:
            mock_logger.warning.assert_not_called()
