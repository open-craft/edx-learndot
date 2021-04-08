"""
This module makes it easier to use Learndot's API.

Right now it just contains what's required to support updating
Learndot enrolments when an edX learner passes a course, and that's
all based on their `v2 API`_.

Note that the 'enrolment' spelling is intentional; that's the way
Learndot (and (TIL) the rest of the English-speaking world outside of
America) spell it, and it makes it easy to distinguish between their
enrolments and edX enrollments.

.. _v2 API:
    https://trainingrocket.atlassian.net/wiki/spaces/DOCS/pages/74416315/API+V2
"""

from __future__ import absolute_import, unicode_literals

import functools
import hashlib
import logging
import os

import dateutil.parser
import requests
from retrying import retry
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError

from edxlearndot.models import EnrolmentStatusLog

log = logging.getLogger(__name__)


LEARNDOT_RETRY_WAIT = getattr(settings, 'LEARNDOT_RETRY_WAIT_SECONDS', 5) * 1000
LEARNDOT_RETRY_MAX_ATTEMPTS = getattr(settings, 'LEARNDOT_RETRY_MAX_ATTEMPTS', 10)

def cmp(a, b):
    """
    Compares elements of two lists

    Compare the two objects x and y and return an integer according
    to the outcome.

    The return value is:
        - negative if x < y
        - zero if x == y
        - strictly positive if x > y
    """
    return (a > b) - (a < b)

class LearndotAPIException(Exception):
    """
    A wrapper around exceptions encountered while using the API.
    """

    @classmethod
    def retry_match(cls, exception):
        """
        Return True to indicate that we should retry on these API errors:
            429 Too Many Requests
            504 Gateway Timeout
        """
        str_e = str(exception)
        if (isinstance(exception, cls) and (
                ("429" in str_e) or ("504" in str_e) or ("502" in str_e))):
            log.warning("Retrying...")
            return True
        return False


def extract_enrolment_sort_key(e):
    """
    Return a key for sorting enrolments.

    We're generally interested in the latest ``expiryDate``, so that's
    the first component of the key. It is possible for enrolments to
    lack ``expiryDate``, if the associated component doesn't have
    ``expiryDays`` set. In this case, we'll fall back to sorting by
    the enrolment's ``modified`` date, then to its ``created`` date,
    or if those are somehow missing, an empty string.

    Arguments:
        e: a dict parsed from a Learndot JSON enrolment

    Returns:
        key: a tuple of (expiryDate, modified or created or "")

    Raises:
        ValueError: if an expiry date can't be parsed
        OverflowError: if an expiry date can't be fit into the largest valid C integer
    """

    key = (e.get("expiryDate") or "", e.get("modified") or e.get("created") or "")

    # validate each date string if not empty
    for ds in key:
        if ds != "":
            dateutil.parser.parse(ds)

    return key


def compare_enrolment_sort_keys(t1, t2):
    """
    Compare enrolments by expiry date.

    An enrolment with no expiryDate should sort after one that
    expires.

    Arguments:
        t1: a tuple of ISO8601 date strings, each possibly empty
        t2: a tuple of ISO8601 date strings, each possibly empty

    Returns:
        -1 if t1 < t2, 1 if t1 > t2, or 0 if they're equal
    """

    t1l = len(t1)
    t2l = len(t2)
    for i in range(max(t1l, t2l)):
        ds1 = t1[i] if i < t1l else ""
        ds2 = t2[i] if i < t2l else ""

        if ds1 == "" and ds2 != "":
            return 1
        elif ds1 != "" and ds2 == "":
            return -1
        else:
            r = cmp(ds1, ds2)
            if r != 0:
                return r

    return 0


def extract_and_compare_enrolment_sort_keys(enrolment1, enrolment2):
    """
    Extracts key for sorting enrolments then compares those enrolment keys

    This function is a combination of both `compare_enrolment_sort_keys` and
    `extract_enrolment_sort_key` such that it can be used with `functools.cmp_to_key`

    Arguments:
        enrolment1: a dict parsed from a Learndot JSON enrolment
        enrolment2: a dict parsed from a Learndot JSON enrolment

    Returns:
        Output of `compare_enrolment_sort_keys`, which is
        -1 if t1 < t2, 1 if t1 > t2, or 0 if they're equal
    """
    enrolment1_expiry = extract_enrolment_sort_key(enrolment1)
    enrolment2_expiry = extract_enrolment_sort_key(enrolment2)

    return compare_enrolment_sort_keys(enrolment1_expiry, enrolment2_expiry)

def sort_enrolments_by_expiry(enrolment_list):
    """
    Sorts an array of Learndot enrolments by expiry date.

    Learndot presents timestamps like expiryDate in ISO8601, without
    the T separator (as permitted), e.g. "2019-03-09 05:52:11". This
    works well enough for sorting. It is possible for enrolments to
    lack an ``expiryDate``; `extract_enrolment_sort_key` documents
    handling of those cases.

    Arguments:
        enrolment_list (list): a list of dictionaries representing
            Learndot enrolments, as parsed from their API response.

    Returns:
        list: the input list, sorted by expiry date

    Raises:
        ValueError: if a sorting date can't be parsed
        OverflowError: if a sorting date can't be fit into the largest valid C integer
    """
    return sorted(enrolment_list, key=functools.cmp_to_key(extract_and_compare_enrolment_sort_keys))


class EnrolmentStatus:
    """
    Basically an enum of valid Learndot enrolment status values.

    Provides the convenience method `is_valid`.
    """
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    MISSED = "MISSED"
    PASSED = "PASSED"
    TENTATIVE = "TENTATIVE"

    @classmethod
    def is_valid(cls, status):
        return hasattr(cls, status) and getattr(cls, status) == status


class LearndotAPIClient:
    """
    Client for the live Learndot API.
    """

    def get_api_key(self):
        """
        Returns the API key for the Learndot v2 API.
        """
        try:
            return settings.LEARNDOT_API_KEY
        except AttributeError as attr_error:
            msg = (
                "The Learndot API key could not be found in your Django settings. "
                "Please add it as settings.LEARNDOT_API_KEY."
            )
            log.fatal(msg)
            raise LearndotAPIException(msg) from attr_error

    def get_api_base_url(self):
        """
        Returns the base URL for the Learndot v2 API.
        """
        try:
            return settings.LEARNDOT_API_BASE_URL
        except AttributeError as attr_error:
            msg = (
                "The Learndot API base URL could not be found in your Django settings. "
                "Please add it as settings.LEARNDOT_API_BASE_URL."
            )
            log.fatal(msg)
            raise LearndotAPIException(msg) from attr_error

    def get_api_request_headers(self):
        """
        Returns the headers required for v2 API calls.
        """
        return {
            "TrainingRocket-Authorization": self.get_api_key(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @retry(retry_on_exception=LearndotAPIException.retry_match,
           wait_fixed=LEARNDOT_RETRY_WAIT,
           stop_max_attempt_number=LEARNDOT_RETRY_MAX_ATTEMPTS)
    def get_contact_id(self, user):
        """
        Tries to look up a Learndot contact using the edX user record.

        Arguments:
            user: django.contrib.auth.models.User

        Returns:
            int: the numeric Learndot contact ID.

        Raises:
            LearndotAPIException: if Requests throws anything, or if
                multiple contacts are found.
        """

        log.info("Looking up Learndot contact for user %s.", user)

        contact_query = {"email": [user.email]}

        hashed_email = hashlib.md5(user.email.encode('utf-8')).hexdigest()
        contact_cache_key = 'edxlearndot-contact-{}-{}'.format(hashed_email, user.id)

        cached_contact_id = cache.get(contact_cache_key)
        if cached_contact_id is not None:
            log.info("Using cached contact ID %s", cached_contact_id)
            return cached_contact_id

        response = requests.post(
            self.get_contact_search_url(),
            headers=self.get_api_request_headers(),
            json=contact_query
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = "Error looking up Learndot contact for user {}: {}".format(user, e)
            log.error(msg)
            raise LearndotAPIException(msg) from e

        contacts = response.json()["results"]
        contact_id = None

        # Learndot API query doesn't use exact matching, so filter out any contacts whose emails don't match.
        contacts = [c for c in contacts if c["email"] == user.email]

        if len(contacts) == 1:
            contact_id = contacts[0]["id"]
        elif len(contacts) > 1:
            surfeit = {c["id"]: (c["_displayName_"], c["email"]) for c in contacts}
            msg = "Multiple Learndot contacts found for user {}: {}".format(user, surfeit)
            log.error(msg)

        if contact_id is not None:
            log.info("Caching Learndot contact ID %s for user %s", contact_id, user)
            cache.set(contact_cache_key, contact_id)

        return contact_id

    def get_contact_search_url(self):
        """
        Returns the URL used to find contacts.
        """
        return os.path.join(self.get_api_base_url(), "api/rest/v2/manage/contact/search")

    def get_enrolment_search_url(self):
        """
        Returns the URL used to find enrolments.
        """
        return os.path.join(self.get_api_base_url(), "api/rest/v2/manage/enrolment/search")

    def get_enrolment_management_url(self, enrolment_id):
        """
        Returns a template for the URL used to update enrolments.

        The template URL contains a placeholder into which a numeric
        enrolment ID should be substituted.
        """
        return os.path.join(
            self.get_api_base_url(),
            "api/rest/v2/manage/enrolment/{}".format(enrolment_id)
        )

    @retry(retry_on_exception=LearndotAPIException.retry_match,
           wait_fixed=LEARNDOT_RETRY_WAIT,
           stop_max_attempt_number=LEARNDOT_RETRY_MAX_ATTEMPTS)
    def get_enrolment_id(self, contact_id, component_id):
        """
        Fetches the most recent Learndot enrolment record.

        Obtain the contact ID with `edxlearndot.learndot.get_contact_id`,
        and the component ID associated with an edX course by querying
        `edxlearndot.models.CourseMapping`.

        Arguments:
            contact_id (int): the numeric Learndot contact ID.
            component_id (int): the numeric Learndot component ID.

        Returns:
            int: the numeric Learndot enrolment ID.

        Raises:
            LearnDotAPIException: if multiple enrollments were found, but
                could not be sorted so that the latest one could be determined.
        """

        log.info("Looking up Learndot enrolment for contact %s, component %s.", contact_id, component_id)

        enrolment_cache_key = 'edxlearndot-enrolment-{}-{}'.format(contact_id, component_id)

        cached_enrolment_id = cache.get(enrolment_cache_key)
        if cached_enrolment_id is not None:
            log.info("Using cached enrolment ID %s", cached_enrolment_id)
            return cached_enrolment_id

        enrolment_query = {
            "contactId": [contact_id],
            "componentId": [component_id]
        }

        response = requests.post(
            self.get_enrolment_search_url(),
            headers=self.get_api_request_headers(),
            json=enrolment_query
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = "Error looking up Learndot enrolment for contact {}, component {}: {}".format(
                contact_id,
                component_id,
                e
            )
            log.error(msg)
            raise LearndotAPIException(msg) from e

        enrolments = [e for e in response.json()["results"] if e["status"] != "CANCELLED"]
        enrolment_id = None
        if len(enrolments) == 1:
            enrolment_id = enrolments[0]["id"]
        elif len(enrolments) > 1:
            try:
                enrolment_id = sort_enrolments_by_expiry(enrolments)[-1]["id"]
                log.info(
                    (
                        "Multiple enrolments exist for contact %s, component %s. "
                        "Choosing the one with the latest expiry date: %s"
                    ),
                    contact_id,
                    component_id,
                    enrolment_id
                )
            except (ValueError, OverflowError) as e:
                msg = (
                    "Multiple enrolments exist for contact {}, component {}, but they could not be sorted "
                    "by expiry date to determine the latest one. The error raised while sorting was: {}"
                ).format(contact_id, component_id, e)
                log.error(msg)
                raise LearndotAPIException(msg) from e

        if enrolment_id is not None:
            log.info(
                "Caching Learndot enrolment ID %s for contact %s, component %s",
                enrolment_id, contact_id, component_id
            )
            cache.set(enrolment_cache_key, enrolment_id)

        return enrolment_id

    @retry(retry_on_exception=LearndotAPIException.retry_match,
           wait_fixed=LEARNDOT_RETRY_WAIT,
           stop_max_attempt_number=LEARNDOT_RETRY_MAX_ATTEMPTS)
    def set_enrolment_status(self, enrolment_id, status, unconditional=False):
        """
        Sets the status of a Learndot enrollment record.

        Arguments:
            enrolment_id (int): the numeric Learndot enrollment ID

            status (str): a status string which must be valid according to
                          `edxlearndot.learndotapi.EnrolmentStatus`.

            unconditional (bool): whether to unconditionally send the new
                                  status to Learndot, instead of checking
                                  EnrolmentStatusLog records to see if it
                                  has already been sent.
        Returns:
            None

        Raises:
            LearndotAPIException: if the requested status is invalid, or
                Requests throws anything.
        """
        if not enrolment_id:
            msg = "Enrolment_id can not be None"
            log.error(msg)
            raise LearndotAPIException(msg)

        log.info("Setting Learndot enrolment status to %s for enrolment %s.", status, enrolment_id)

        if not EnrolmentStatus.is_valid(status):
            msg = "Invalid enrolment status \"{}\".".format(status)
            log.error(msg)
            raise LearndotAPIException(msg)

        if not unconditional:
            try:
                enrolment_status = EnrolmentStatusLog.objects.get(learndot_enrolment_id=enrolment_id)
                if enrolment_status.status == status:
                    log.info(
                        "Learndot enrolment was logged as set to %s at %s, so skipping update.",
                        enrolment_status.status,
                        enrolment_status.updated_at
                    )
                    return
            except EnrolmentStatusLog.DoesNotExist:
                pass

        response = requests.post(
            self.get_enrolment_management_url(enrolment_id),
            headers=self.get_api_request_headers(),
            json={"status": status}
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = "Error trying to set status of enrolment {} to {}: {}".format(enrolment_id, status, e)
            log.error(msg)
            raise LearndotAPIException(msg) from e

        try:
            enrolment_status_log, _created = EnrolmentStatusLog.objects.get_or_create(
                learndot_enrolment_id=enrolment_id
            )
            enrolment_status_log.status = status
            enrolment_status_log.save()
            log.info(
                "Recorded status of enrolment %s as %s at %s",
                enrolment_status_log.learndot_enrolment_id,
                enrolment_status_log.status,
                enrolment_status_log.updated_at
            )
        except (IntegrityError, MultipleObjectsReturned) as e:
            log.error("Error recording enrolment status update: %s", e)

    def set_enrolment_status_to_passed(self, enrolment_id, unconditional=False):
        """
        Sets the status of a Learndot enrollment record to PASSED.
        Arguments:
            enrolment_id (int): the numeric Learndot enrollment ID
            unconditional (bool): whether to unconditionally send the new
                                  status to Learndot, instead of checking
                                  EnrolmentStatusLog records to see if it
                                  has already been sent.
        Returns:
            None
        Raises:
            LearndotAPIException: if the requested status is invalid, or
                Requests throws anything.
        """
        self.set_enrolment_status(enrolment_id, EnrolmentStatus.PASSED, unconditional)

    def check_if_enrolment_and_set_status_to_passed(self, contact_id, component_id, unconditional=False):
        """
        Sets the status of a Learndot enrollment record to PASSED if enrollment_id is found.
        Arguments:
            contact_id (int): the numeric Learndot enrollment ID
            component_id (int): the numeric Learndot component ID.
            unconditional (bool): whether to unconditionally send the new
                                  status to Learndot, instead of checking
                                  EnrolmentStatusLog records to see if it
                                  has already been sent.
        Returns:
            None
        Raises:
            LearndotAPIException: if the requested status is invalid, or
                Requests throws anything.
        """
        enrolment_id = self.get_enrolment_id(contact_id, component_id)
        if not enrolment_id:
            log.error("No enrolment found for contact %s, component %s", contact_id, component_id)
            return
        self.set_enrolment_status(enrolment_id, EnrolmentStatus.PASSED, unconditional=unconditional)
