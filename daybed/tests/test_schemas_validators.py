import mock
import colander
from cornice.errors import Errors
from pyramid.testing import DummyRequest
from pyramid.security import Authenticated

from daybed.schemas.validators import (validator, RolesSchema,
                                       PolicySchema)
from daybed.tests.support import unittest
from daybed.acl import PERMISSION_FULL


class ValidatorTests(unittest.TestCase):
    def test_adds_body_error_if_json_invalid(self):
        request = DummyRequest()
        request.body = b'{wrong,"format"}'
        request.errors = Errors()
        validator(request, mock.Mock())
        self.assertEqual('body', request.errors[0]['location'])


class RolesSchemaTests(unittest.TestCase):
    def test_roles(self):
        schema = RolesSchema()
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


class PolicySchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = PolicySchema()

    def test_key_with_single_permission_is_valid(self):
        simple = {
            'role:creator': {'definition': {'create': True}}
        }
        self.assertEquals(simple, self.schema.deserialize(simple))

    def test_wrong_permission_name_is_valid(self):
        wrong = {
            'role:creator': {'definition': {'create': True, 'sing': True}}
        }
        self.assertRaises(colander.Invalid, self.schema.deserialize, wrong)

    def test_policy_apply_to_several_roles(self):
        policy = {'role:admins': PERMISSION_FULL,
                  Authenticated: {'definition': {'read': True},
                                  'records': {'read': True}}}
        self.assertEquals(policy, self.schema.deserialize(policy))

    def test_empty_is_valid(self):
        self.assertEquals({}, self.schema.deserialize({}))

    def test_can_have_description(self):
        policy = {'description': 'Useful for polls'}
        self.assertEquals(policy, self.schema.deserialize(policy))

    def test_can_have_title(self):
        policy = {'title': 'Open to everyone'}
        self.assertEquals(policy, self.schema.deserialize(policy))

    def test_can_have_both_title_and_roles(self):
        policy = {'title': 'Open to everyone', 'role:admins': PERMISSION_FULL}
        self.assertEquals(policy, self.schema.deserialize(policy))
