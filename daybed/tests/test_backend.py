try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # flake8: noqa
from collections import defaultdict
from uuid import uuid4

import mock
import six
from couchdb.client import Server
from couchdb.design import ViewDefinition

from daybed.backends.exceptions import (
    UserAlreadyExist, PolicyNotFound, ModelNotFound, RecordNotFound,
)
from daybed.backends.couchdb.backend import (
    CouchDBBackendConnectionError, CouchDBBackend
)
from daybed.backends.couchdb.database import Database as CouchDBDatabase
from daybed.backends.couchdb.views import docs as couchdb_views
from daybed.backends.memory.database import Database as MemoryDatabase


class BackendTestBase(object):
    """Test that the backends work as expected.

    This class is the base one, you can extend it with the name of the backend
    you want to test.  Since all the backend implementations share the same
    interface, all the tests should pass in the same way.
    """
    def setUp(self):
        self.roles = {
            'admins': ['group:pirates', 'group:flibustiers'],
            'users': ['Remy', 'Alexis']}

        self.definition = {
            "title": "simple",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False}]
        }
        self.policy = {'role:admins': {'definition': {'create':True}}}

        self.record = {'age': 7}

    def _create_model(self, name='modelname'):
        self.db.set_policy('admin-only', self.policy)
        self.db.put_model(self.definition, self.roles, 'admin-only', name)

    def test_put_roles_unknown(self):
        self.assertRaises(ModelNotFound, self.db.get_roles, 'unknown')

    def test_put_roles(self):
        self._create_model()
        self.db.put_roles('modelname', self.roles)
        self.assertEquals(self.db.get_roles('modelname'), self.roles)

    def test_add_role_works(self):
        self._create_model()
        self.db.add_role('modelname', 'authors', ['Benoit'])
        roles = self.roles.copy()
        roles.update({'authors': ['Benoit']})
        self.assertDictEqual(self.db.get_roles('modelname'), roles)

    def test_add_role_merges_redundant_users(self):
        self._create_model()
        # Test that when we add an user to an existing role they get merged.
        self.db.put_roles('modelname', self.roles)
        self.db.add_role('modelname', 'admins', ['Benoit'])
        self.assertIn('Benoit', self.db.get_roles('modelname')['admins'])

        # test that if we add it twice it's present just once.
        self.db.add_role('modelname', 'admins', ['Benoit'])
        self.assertEqual(len([a for a in
                              self.db.get_roles('modelname')['admins']
                              if a == 'Benoit']), 1)

    def test_add_group_works(self):
        self.db.add_user({'name': 'Remy'})
        self.db.add_group('Remy', 'admins')
        user = self.db.get_user('Remy')
        self.assertEquals(user['groups'], ['admins'])

    def test_add_user_adds_the_group_if_not_provided(self):
        self.db.add_user({'name': 'Remy'})
        user = self.db.get_user('Remy')
        self.assertEquals(user['groups'], [])

    def test_get_groups_works(self):
        self.db.add_user({'name': 'Remy', 'groups': ['toto', 'tata']})
        self.assertEquals(self.db.get_groups('Remy'), ['toto', 'tata'])

    def test_add_user_fails_if_already_exist(self):
        self.db.add_user({'name': 'Remy'})
        self.assertRaises(UserAlreadyExist, self.db.add_user, {'name': 'Remy'})

    def test_set_policy(self):
        self.db.set_policy('admin-only', self.policy)
        self.assertDictEqual(self.db.get_policy('admin-only'), self.policy)

    def test_get_policy_return_non_when_unknown(self):
        self.assertRaises(PolicyNotFound, self.db.get_policy, 'unknown')

    def test_get_model_policy(self):
        self._create_model()
        self.assertEqual(self.db.get_model_policy('modelname'), self.policy)

    def test_get_model_policy_id(self):
        self._create_model()
        self.assertEqual(self.db.get_model_policy_id('modelname'),
                         'admin-only')

    def test_put_record(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['Alexis'])

        # When we put a new version of a record, we should keep the list of
        # authors.
        item_id = self.db.put_record('modelname', self.record, ['Remy'])
        self.db.put_record('modelname', self.record, ['Alexis'], item_id)

        authors = self.db.get_record_authors('modelname', item_id)
        self.assertEquals(set(authors), set(['Alexis', 'Remy']))

    def test_get_records(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['author'])
        self.assertEqual(len(self.db.get_records('modelname')), 1)

    def test_get_records_empty(self):
        self._create_model()
        self.assertEqual(self.db.get_records('modelname'), [])

    def test_get_record(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['author'], 'record')
        self.assertEqual(self.db.get_record('modelname', 'record'),
                         self.record)

    def test_get_record_authors(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['author'], 'record')
        self.assertEqual(self.db.get_record_authors('modelname', 'record'),
                         ['author'])

    def test_delete_record(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['author'], 'record')
        self.db.delete_record('modelname', 'record')
        self.assertRaises(RecordNotFound, self.db.get_record,
                          'modelname', 'record')

    def test_put_model_raises_if_policy_unknown(self):
        self.assertRaises(PolicyNotFound, self.db.put_model, self.definition,
                          self.roles, 'unknown')

    def test_get_model_definition(self):
        self._create_model()
        self.assertEquals(self.db.get_model_definition('modelname'),
                          self.definition)

    def test_delete_model(self):
        self._create_model()
        self.db.delete_model('modelname')
        self.assertRaises(ModelNotFound, self.db.get_model_definition,
                          'modelname')

    def test_model_deletion_raises_if_unknwon(self):
        self.assertRaises(ModelNotFound, self.db.delete_model, 'unknown')

    def test_policies(self):
        policies = self.db.get_policies()
        self.assertTrue(isinstance(policies, list))


class TestCouchDBBackend(BackendTestBase, TestCase):

    def setUp(self):
        self.server = Server('http://localhost:5984')
        self.db_name = 'test_%s' % uuid4()
        self.server.create(self.db_name)

        db = self.server[self.db_name]
        ViewDefinition.sync_many(db, couchdb_views)
        self.db = CouchDBDatabase(db, lambda: six.text_type(uuid4()))
        super(TestCouchDBBackend, self).setUp()

    def tearDown(self):
        del self.server[self.db_name]

    def test_server_unreachable(self):
        config = mock.Mock()
        config.registry = mock.Mock()
        config.registry.settings = defaultdict(str)
        config.registry.settings['backend.db_host'] = 'http://unreachable/'
        config.registry.settings['backend.db_name'] = 'daybed'

        with self.assertRaises(CouchDBBackendConnectionError):
            CouchDBBackend(config)


class TestMemoryBackend(BackendTestBase, TestCase):

    def setUp(self):
        empty = {
            'models': {},
            'data': {},
            'users': {},
            'policies': {}
        }
        self.db = MemoryDatabase(empty, lambda: six.text_type(uuid4()))
        super(TestMemoryBackend, self).setUp()
