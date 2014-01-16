try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # flake8: noqa
import mock

from pyramid.security import Authenticated

from daybed.acl import (DaybedAuthorizationPolicy, build_user_principals,
                        PERMISSION_FULL, CRUD, get_binary_mask)


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
        policy = {'group:admins': PERMISSION_FULL,
                  'authors:': {'records': CRUD},
                  Authenticated: {'definition': {'read': True}}}
        context.db.get_model_policy.return_value = policy

        self.assertFalse(permits(context, ['Alexis'], 'get_definition'))
        self.assertTrue(permits(context, ['Alexis', Authenticated],
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


class PermissionAsMaskTest(TestCase):
    def test_no_permissions_is_blank_mask(self):
        mask = get_binary_mask({})
        self.assertEquals(mask, 0)

    def test_single_permission_has_single_byte(self):
        mask = get_binary_mask({'records': {'read': True}})
        self.assertEquals(mask, 0x0400)

    def test_full_permission_is_full_byte(self):
        mask = get_binary_mask({'records': {'create': True,
                                            'read': True,
                                            'update': True,
                                            'delete': True}})
        self.assertEquals(mask, 0x0F00)

    def test_all_permissions_is_full_mask(self):
        mask = get_binary_mask(PERMISSION_FULL)
        self.assertEquals(mask, 0xFFFF)
