import colander

import mock
from daybed import schemas
from daybed.tests.support import BaseWebTest


class FakeRequest(object):
    authenticated_userid = "myHawkId"


class UserIdTest(BaseWebTest):

    def test_user_id_definition(self):
        schema = schemas.UserIdField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'userid'})
        self.assertTrue(isinstance(definition, dict))

    @mock.patch('daybed.schemas.identity.get_current_request')
    def test_non_existing_user_id_record(self, get_current_request):
        schema = schemas.UserIdField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'userid'})

        get_current_request.return_value = FakeRequest()

        validator = schemas.UserIdField.validation(**definition)
        self.assertEqual('myHawkId', validator.deserialize(''))

    @mock.patch('daybed.schemas.identity.get_current_request')
    def test_existing_user_id_record(self, get_current_request):
        schema = schemas.UserIdField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'userid'})

        get_current_request.return_value = FakeRequest()
        self.db.set_user_id("myHawkId", "alexis@example.com")

        validator = schemas.UserIdField.validation(**definition)
        self.assertEqual('alexis@example.com', validator.deserialize(''))

    @mock.patch('daybed.schemas.identity.get_current_request')
    def test_non_existing_user_id_record_with_value(self, get_current_request):
        schema = schemas.UserIdField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'userid'})

        get_current_request.return_value = FakeRequest()

        validator = schemas.UserIdField.validation(**definition)
        self.assertEqual('myHawkId', validator.deserialize('myHawkId'))

    @mock.patch('daybed.schemas.identity.get_current_request')
    def test_existing_user_id_record_with_value(self, get_current_request):
        schema = schemas.UserIdField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'userid'})

        get_current_request.return_value = FakeRequest()
        self.db.set_user_id("myHawkId", "alexis@example.com")

        validator = schemas.UserIdField.validation(**definition)
        self.assertEqual('alexis@example.com',
                         validator.deserialize('alexis@example.com'))

    @mock.patch('daybed.schemas.identity.get_current_request')
    def test_existing_user_id_record_with_wrong_value(self,
                                                      get_current_request):
        schema = schemas.UserIdField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'userid'})

        get_current_request.return_value = FakeRequest()
        self.db.set_user_id("myHawkId", "alexis@example.com")

        validator = schemas.UserIdField.validation(**definition)

        self.assertRaises(colander.Invalid, validator.deserialize, 'boom')

        try:
            validator.deserialize('boom')
        except colander.Invalid as exp:
            self.assertEquals(
                exp.messages()[0],
                "boom is a wrong user_id, it should be alexis@example.com.")
