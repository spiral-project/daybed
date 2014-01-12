import mock
import colander
from cornice.errors import Errors
from pyramid.testing import DummyRequest

from daybed.schemas.validators import validator, RolesValidator
from daybed.tests.support import unittest


class ValidatorTests(unittest.TestCase):
    def test_adds_body_error_if_json_invalid(self):
        request = DummyRequest()
        request.body = b'{wrong,"format"}'
        request.errors = Errors()
        validator(request, mock.Mock())
        self.assertEqual('body', request.errors[0]['location'])


class RolesValidatorTests(unittest.TestCase):
    def test_roles(self):
        schema = RolesValidator()
        self.assertRaises(colander.Invalid, schema.deserialize, {})
        self.assertRaises(colander.Invalid, schema.deserialize,
                          {'admins': 'not-a-sequence'})
        self.assertEquals(schema.deserialize(
            {'admins': ['Remy', 'Alexis']}),
            {'admins': ['Remy', 'Alexis']})

        return
        # XXX: FIXME
        self.assertRaises(colander.Invalid, schema.deserialize,
                          {'admins': ['Test'],
                           'group:toto': 'not-a-sequence'})
