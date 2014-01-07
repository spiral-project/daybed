try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # flake8: noqa
import mock


from daybed.acl import DaybedAuthorizationPolicy, build_user_principals


class TestACL(TestCase):

    def _get_request(self):
        request = mock.MagicMock()
        request.matchdict = {'model_id': 'modelname',
                             'record_id': 'record_id'}

        db = mock.MagicMock()
        db.get_groups.return_value = ['dumb-people']
        db.get_roles.return_value = {'admins': ['group:dumb-people', 'Benoit']}
        db.get_record_authors.return_value = ['Alexis', 'Remy']
        request.db = db
        return request

    def test_acl_permits(self):
        authz_policy = DaybedAuthorizationPolicy()
        permits = authz_policy.permits

        context = mock.MagicMock()
        policy = {'group:admins': 0xFFFF,
                  'authors:': 0x0F00,
                  'system.Authenticated': 0x4000}
        context.db.get_model_policy.return_value = policy

        self.assertFalse(permits(context, ['Alexis'], 'get_definition'))
        self.assertTrue(permits(context, ['Alexis', 'system.Authenticated'],
                                'get_definition'))

    def test_build_user_principals_resolve_group(self):
        principals = build_user_principals('Chuck Norris', self._get_request())
        self.assertEquals(set([u'role:admins', u'group:dumb-people']),
                          principals)

    def test_build_user_principals_resolve_role(self):
        request = self._get_request()
        request.db.get_groups.return_value = []
        principals = build_user_principals('Benoit', request)
        self.assertEquals(set([u'role:admins']), principals)

    def test_build_user_principals_resolve_author(self):
        request = self._get_request()
        request.db.get_groups.return_value = []
        principals = build_user_principals('Alexis', request)
        self.assertEquals(set([u'authors:']), principals)
