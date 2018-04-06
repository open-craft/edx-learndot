""" This is utils module for tests """
import responses

from django.test import override_settings

from edxlearndot.learndot import LearndotAPIClient, EnrolmentStatus


class LearndotAPIClientMock(LearndotAPIClient):
    """
    Mock client for tests.
    """

    @override_settings(LEARNDOT_API_KEY='test')
    def get_api_key(self):
        return super(LearndotAPIClientMock, self).get_api_key()
    
    @override_settings(LEARNDOT_API_BASE_URL='https://localhost/learndot/v2/api')
    def get_api_base_url(self):
        return super(LearndotAPIClientMock, self).get_api_base_url()

    @responses.activate
    def get_contact_id(self, user):
        """
        Mock response returns for get_contact.
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
        Mock response for get_enrolment.
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
        Mock response from POST request.
        """
        response = responses.add(
            responses.POST,
            self.get_enrolment_management_url(enrolment_id)
        )
        return super(LearndotAPIClientMock, self).set_enrolment_status(enrolment_id, status)
