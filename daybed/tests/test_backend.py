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
    TokenAlreadyExist, ModelNotFound, RecordNotFound,
)
from daybed.backends.couchdb import (
    CouchDBBackendConnectionError, CouchDBBackend
)
from daybed.backends.memory import MemoryBackend
from daybed.backends.redis import RedisBackend
from redis.exceptions import ConnectionError

from daybed.backends.couchdb.views import docs as couchdb_views


class BackendTestBase(object):
    """Test that the backends work as expected.

    This class is the base one, you can extend it with the name of the backend
    you want to test.  Since all the backend implementations share the same
    interface, all the tests should pass in the same way.
    """
    def setUp(self):
        self.acls = {
            'read_definition': ['Remy', 'Alexis']
        }

        self.definition = {
            "title": "simple",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False}]
        }
        self.record = {'age': 7}

    def _create_model(self, model_id='modelname'):
        self.db.put_model(self.definition, self.acls, model_id)

    def test_add_acls_merges_redundant_acls(self):
        pass

    def test_add_token_fails_if_already_exist(self):
        self.db.add_token("Remy", "Foo")
        self.assertRaises(TokenAlreadyExist, self.db.add_token, "Remy", "Bar")


    def test_get_model_acls(self):
        self._create_model()
        self.assertEqual(self.db.get_model_acls('modelname'), {
            'read_definition': ['Remy', 'Alexis']
        })

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
        records = self.db.get_records('modelname')
        self.assertEqual(len(records), 1)
        self.assertIn('id', records[0])
        del records[0]['id']
        self.assertDictEqual(records[0], {u'age': 7})

    def test_get_records_with_authors(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['author'])
        records = self.db.get_records('modelname', with_authors=True)
        self.assertEqual(len(records), 1)
        self.assertIn('id', records[0]['record'])
        del records[0]['record']['id']
        self.assertDictEqual(records[0], {'authors': [u'author'], 'record': {u'age': 7}})

    def test_get_records_empty(self):
        self._create_model()
        self.assertEqual(self.db.get_records('modelname'), [])

    def test_get_record(self):
        self._create_model()
        self.db.put_record('modelname', self.record, ['author'], 'record')
        record = self.record.copy()
        record["id"] = "record"
        self.assertEqual(self.db.get_record('modelname', 'record'), record)

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

    def test_get_model_definition(self):
        self._create_model()
        self.assertEquals(self.db.get_model_definition('modelname'),
                          self.definition)

    def test_delete_model(self):
        self._create_model("modelname")
        self.db.put_record("modelname", self.record, ['Remy'], "123456")

        resp = self.db.delete_model('modelname')
        self.assertEqual(resp, {
            "definition": self.definition,
            "acls": self.acls,
            "records": [{"age": 7, "id": "123456"}]
        })
        self.assertRaises(ModelNotFound, self.db.get_model_definition,
                          'modelname')
        self.assertRaises(ModelNotFound, self.db.get_records,
                          'modelname')
        self.assertRaises(RecordNotFound, self.db.get_record,
                          'modelname', '123456')

    def test_model_deletion_raises_if_unknown(self):
        self.assertRaises(ModelNotFound, self.db.delete_model, 'unknown')


class TestCouchDBBackend(BackendTestBase, TestCase):

    def setUp(self):
        self.db = CouchDBBackend(
            host='http://localhost:5984',
            db_name='test_%s' % uuid4(),
            id_generator=lambda: six.text_type(uuid4())
        )
        super(TestCouchDBBackend, self).setUp()

    def tearDown(self):
        self.db.delete_db()

    def test_server_unreachable(self):
        with self.assertRaises(CouchDBBackendConnectionError):
            CouchDBBackend(
                host='http://unreachable', db_name='daybed',
                id_generator=lambda: True
            )


class TestRedisBackend(BackendTestBase, TestCase):

    def setUp(self):
        self.db = RedisBackend(
            host='localhost',
            port=6379,
            db=5,
            id_generator=lambda: six.text_type(uuid4())
        )
        super(TestRedisBackend, self).setUp()

    def tearDown(self):
        self.db.delete_db()

    def test_server_unreachable(self):
        with self.assertRaises(ConnectionError):
            db = RedisBackend(
                host='unreachable', port=6379, db=5,
                id_generator=lambda: True
            )

class TestMemoryBackend(BackendTestBase, TestCase):

    def setUp(self):
        self.db = MemoryBackend(lambda: six.text_type(uuid4()))
        super(TestMemoryBackend, self).setUp()
