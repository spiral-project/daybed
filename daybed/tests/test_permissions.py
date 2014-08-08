try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # flake8: noqa
import mock

from pyramid.security import Authenticated

from daybed.permissions import (
    All, Any, DaybedAuthorizationPolicy, build_user_principals,
    invert_acls_matrix, dict_set2list, dict_list2set
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

class TestACL(TestCase):

    def _get_request(self):
        request = mock.MagicMock()
        request.matchdict = {'model_id': 'modelname',
                             'record_id': 'record_id'}

        db = mock.MagicMock()
        db.get_record_authors.return_value = ['Alexis', 'Remy']
        request.db = db
        return request

    def test_acl_permits(self):
        authz_policy = DaybedAuthorizationPolicy()
        permits = authz_policy.permits

        context = mock.MagicMock()
        context.db.get_model_acls.return_value = {
            'read_definition': [Authenticated]
        }

        self.assertFalse(permits(context, ['Alexis'], 'get_definition'))
        self.assertTrue(permits(context, ['Alexis', Authenticated],
                                'get_definition'))

    def test_dict_set2list(self):
        self.assertDictEqual(dict_set2list({
            'toto': set(['titi', 'tutu']),
            'titi': set(['tata'])
        }), {'toto': ['titi', 'tutu'], 'titi': ['tata']})

    def test_dict_set2list(self):
        self.assertDictEqual(dict_list2set({
            'toto': ['titi', 'tutu'],
            'titi': ['tata']
        }), {
            'toto': set(['titi', 'tutu']),
            'titi': set(['tata'])
        })

    def test_invert_acls_matrix(self):
        model_acls = {
            'read_acls': ['admin', 'alexis'],
            'update_definition': ['admin'],
            'read_all_records': ['admin', 'remy'],
            'update_my_record': ['admin'],
        }
        tokens_acls = {
            'admin': ['read_acls', 'read_all_records', 'update_definition',
                      'update_my_record'],
            'alexis': ['read_acls'],
            'remy': ['read_all_records']
        }
        self.assertDictEqual(invert_acls_matrix(model_acls), tokens_acls)
