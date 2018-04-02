""" This is utils module for tests """
import responses

from django.test import override_settings

from edxlearndot.learndot import LearndotAPIClient, EnrolmentStatus


class LearndotAPIClientMock(LearndotAPIClient):
    """
    Mock client for tests.
    """
    DOES_NOT_EXIST_ID = 1

    enrolments = {}

    @override_settings(LEARNDOT_API_KEY='test')
    def get_api_key(self):
        return super(LearndotAPIClientMock, self).get_api_key()
    
    @override_settings(LEARNDOT_API_BASE_URL='https://localhost/learndot/v2/api')
    def get_api_base_url(self):
        return super(LearndotAPIClientMock, self).get_api_base_url()

    @responses.activate
    def get_contact_id(self, user):
        """
        Mock implementation just returns the user ID as the contact ID.

        If the user is None, or the user ID is self.DOES_NOT_EXIST_ID,
        the mock contact does not exist.
        """
        responses.add(
            responses.POST,
            self.get_contact_search_url(),
            json={"results": [{"id": 1, "_displayName_": "Test Name", "email": "test@gmail.com"}]}
        )
        return super(LearndotAPIClientMock, self).get_contact_id(user)

    @responses.activate
    def get_enrolment_id(self, contact_id, component_id):
        """
        Mock implementation just returns the concatentation of the two IDs.

        If either is None or self.DOES_NOT_EXIST_ID, the mock
        enrolment does not exist.
        """
        response = responses.add(
            responses.POST,
            self.get_enrolment_search_url(),
            json={"results": [{"id": 1, "status": EnrolmentStatus.IN_PROGRESS}]}
        )
        return super(LearndotAPIClientMock, self).get_enrolment_id(contact_id, component_id)

    @responses.activate
    def set_enrolment_status(self, enrolment_id, status, unconditional=False):
        """
        Stores the status under the given enrolment ID in self.enrolments.
        """
        response = responses.add(
            responses.POST,
            self.get_enrolment_management_url(enrolment_id)
        )
        return super(LearndotAPIClientMock, self).set_enrolment_status(enrolment_id, status)

