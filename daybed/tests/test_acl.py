from unittest import TestCase
import mock


from daybed.acl import DaybedAuthorizationPolicy


class TestACL(TestCase):

    def test_acl_permits(self):
        authz_policy = DaybedAuthorizationPolicy()
        permits = authz_policy.permits

        context = mock.MagicMock()
        policy = {'name': 'admin-only',
                  'type': 'policy',
                  'data': {'group:admins': 0xFFFF,
                           'authors:': 0x0F00,
                           'others:': 0x4000}}
        context.db.get_model_policy.return_value = policy

        self.assertFalse(permits(context, ['Alexis'], 'get_definition'))
        self.assertTrue(permits(context, ['Alexis', 'others:'],
                                'get_definition'))
