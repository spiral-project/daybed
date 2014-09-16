try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # flake8: noqa
import mock

from pyramid.security import Authenticated

from daybed.backends import exceptions
from daybed.permissions import (
    All, Any, DaybedAuthorizationPolicy,
    invert_permissions_matrix, dict_set2list, dict_list2set,
    default_model_permissions, PERMISSIONS_SET, merge_permissions
)


class TestAnyAll(TestCase):

    def test_any(self):
        self.assertTrue(Any(['un', 'deux', 'trois'])
            .matches(['un', 'deux']))

        self.assertTrue(Any(['un', 'deux', 'trois'])
            .matches(['un', 'deux', '4']))

        self.assertFalse(Any(['un', 'deux'])
            .matches(['trois', 'quatre']))

    def test_all(self):
        self.assertFalse(All(['un', 'deux', 'trois'])
            .matches(['un', 'deux']))

        self.assertTrue(All(['un', 'deux'])
            .matches(['un', 'deux']))

        self.assertTrue(All(['un', 'deux'])
            .matches(['un', 'deux', 'trois']))

    def test_nested(self):
        self.assertTrue(Any([All(['un', 'deux']), All(['trois', 'quatre'])])
            .matches(['trois', 'quatre']))

        self.assertTrue(Any([All(['un', 'deux']), All(['trois', 'quatre'])])
            .matches(['un', 'deux']))

        self.assertFalse(Any([All(['un', 'deux']), All(['trois', 'quatre'])])
            .matches(['un', 'trois']))

        self.assertTrue(All([Any(['un', 'deux']), Any(['trois', 'quatre'])])
            .matches(['un', 'trois']))

        self.assertTrue(All([Any(['un', 'deux']), Any(['trois', 'quatre'])])
            .matches(['un', 'deux', 'trois', 'quatre', 'cinq']))

        self.assertFalse(All([Any(['un', 'deux']), Any(['trois', 'quatre'])])
            .matches(['un', 'deux']))


class TestPermissionTools(TestCase):

    def test_default_model_permissions(self):
        perms = default_model_permissions('abc')
        self.assertEqual(set(perms.keys()), PERMISSIONS_SET)
        tokens = [t[0] for t in perms.values()]
        self.assertEqual(set(['abc']), set(tokens))

    def test_nobody_can_change_permissions_of_anonymous_models(self):
        perms = default_model_permissions('system.Everyone')
        self.assertEqual(set(perms.keys()),
                         PERMISSIONS_SET - set(['update_permissions']))

    def test_dict_set2list(self):
        self.assertDictEqual(dict_set2list({
            'toto': set(['titi', 'tutu']),
            'titi': set(['tata'])
        }), {'toto': ['titi', 'tutu'], 'titi': ['tata']})

    def test_dict_set2list_idempotent(self):
        self.assertDictEqual(dict_list2set({
            'toto': ['titi', 'tutu'],
            'titi': ['tata']
        }), {
            'toto': set(['titi', 'tutu']),
            'titi': set(['tata'])
        })

    def test_invert_permissions_matrix(self):
        model_permissions = {
            'read_permissions': ['admin', 'alexis'],
            'update_definition': ['admin'],
            'read_all_records': ['admin', 'remy'],
            'update_my_record': ['admin'],
        }
        credentials_ids_permissions = {
            'admin': ['read_all_records', 'read_permissions',
                      'update_definition', 'update_my_record'],
            'alexis': ['read_permissions'],
            'remy': ['read_all_records']
        }
        self.assertDictEqual(invert_permissions_matrix(model_permissions),
                             credentials_ids_permissions)


class MergePermissionsTest(TestCase):
    def test_from_empty_set(self):
        specified = {"alexis": ["read_permissions"],
                     "remy": ["update_permissions"]}
        result = merge_permissions({}, specified)
        self.assertEqual(result['read_permissions'], ['alexis'])
        self.assertEqual(result['update_permissions'], ['remy'])

    def test_remove(self):
        original = invert_permissions_matrix({
            "alexis": ["create_record", "read_permissions"]
        })
        specified = {
            "alexis": ["-read_permissions"]
        }
        result = merge_permissions(original, specified)
        self.assertNotIn('alexis', result['read_permissions'])
        self.assertIn('alexis', result['create_record'])

    def test_remove_not_present(self):
        original = invert_permissions_matrix({
            "alexis": ["create_record", "read_permissions"]
        })
        specified = {
            "alexis": ["-update_permissions"]
        }
        result = merge_permissions(original, specified)
        self.assertEqual(result['create_record'], ['alexis'])
        self.assertEqual(result['read_permissions'], ['alexis'])

    def test_add_all(self):
        original = invert_permissions_matrix({
            "alexis": ["create_record", "read_permissions"]
        })
        specified = {
            "remy": ["ALL"]
        }
        result = merge_permissions(original, specified)
        result = invert_permissions_matrix(result)

        self.assertDictEqual(result, {
            "alexis": ["create_record", "read_permissions"],
            "remy": sorted(PERMISSIONS_SET)
        })

    def test_remove_all(self):
        original = invert_permissions_matrix({
            "alexis": PERMISSIONS_SET
        })
        specified = {
            "alexis": ["-ALL"]
        }
        result = merge_permissions(original, specified)
        result = invert_permissions_matrix(result)

        self.assertDictEqual(result, {})


class BasePolicyPermissionTest(TestCase):

    def setUp(self):
        self.policy = DaybedAuthorizationPolicy()
        self.context = mock.MagicMock()
        self.context.db.get_model_permissions.return_value = {}

    def permits(self, *args):
        return self.policy.permits(self.context, *args)


class PolicyPermissionTest(BasePolicyPermissionTest):

    def test_pyramid_constants_are_resolved(self):
        policy = DaybedAuthorizationPolicy(model_creators=['Authenticated'])
        self.assertEqual(policy.model_creators, set([Authenticated]))

    def test_allowed_if_principals_in_model_permissions(self):
        self.context.db.get_model_permissions.return_value = {
            'read_definition': [Authenticated]
        }
        self.assertTrue(self.permits(['abc', Authenticated], 'get_definition'))

    def test_not_allowed_if_principals_not_in_model_permissions(self):
        self.context.db.get_model_permissions.return_value = {
            'read_definition': [Authenticated]
        }
        self.assertFalse(self.permits(['abc'], 'get_definition'))

    def test_not_allowed_if_not_author_of_record(self):
        self.context.db.get_model_permissions.return_value = {
            'read_own_records': ['abc']
        }
        self.context.db.get_record_authors.return_value = ['xyz']
        self.assertFalse(self.permits(['abc'], 'get_record'))


class UnknownModelPolicyPermissionTest(BasePolicyPermissionTest):

    def setUp(self):
        super(UnknownModelPolicyPermissionTest, self).setUp()
        e = exceptions.ModelNotFound
        self.context.db.get_model_permissions.side_effect = e

    def test_always_allowed_if_model_unknown(self):
        self.assertTrue(self.permits(['abc'], 'get_definition'))

    def test_not_allowed_to_create_model_if_no_principals(self):
        self.assertFalse(self.permits(['abc'], 'post_model'))

    def test_allowed_to_create_model_if_among_model_creators(self):
        self.policy.model_creators = ['abc']
        self.assertTrue(self.permits(['abc'], 'post_model'))
