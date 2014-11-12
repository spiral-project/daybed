import copy
import base64

import mock
from webtest.app import TestRequest
import elasticsearch

from daybed import __version__ as VERSION, API_VERSION
from daybed.permissions import invert_permissions_matrix
from daybed.backends.exceptions import (
    RecordNotFound, ModelNotFound
)
from daybed.tests.support import BaseWebTest, force_unicode
from daybed.schemas import registry


MODEL_DEFINITION = {
    'definition': {
        "title": "simple",
        "description": "One optional field",
        "fields": [{"name": "age",
                    "hint": "An integer",
                    "label": "Age",
                    "type": "int",
                    "required": False}]
    }
}

MODEL_PERMISSIONS = [
    'create_record',
    'delete_all_records',
    'delete_model',
    'delete_own_records',
    'read_all_records',
    'read_definition',
    'read_own_records',
    'read_permissions',
    'update_all_records',
    'update_definition',
    'update_own_records',
    'update_permissions',
]

MODEL_RECORD = {'age': 42}
MODEL_RECORD2 = {'age': 25}


class FieldsViewTest(BaseWebTest):

    def __init__(self, *args, **kwargs):
        super(FieldsViewTest, self).__init__(*args, **kwargs)
        if not hasattr(self, 'assertCountEqual'):
            self.assertCountEqual = self.assertItemsEqual

    def test_fields_are_listed(self):
        response = self.app.get('/fields')
        fields = response.json
        names = [f.get('name') for f in fields]
        self.assertCountEqual(names, registry.names)
        # String field has no parameters
        stringfield = [f for f in fields if f.get('name') == 'string'][0]
        self.assertIsNone(stringfield.get('parameters'))
        self.assertEquals(stringfield['default_hint'],
                          'A set of characters')
        # Enum field describes list items type
        enumfield = [f for f in fields if f.get('name') == 'enum'][0]
        _type = enumfield['parameters'][0].get('items', {}).get('type')
        self.assertEqual('string', _type)
        # Point field describes GPS with default True
        pointfield = [f for f in fields if f.get('name') == 'point'][0]
        self.assertCountEqual(pointfield['parameters'],
                              [dict(name="gps",
                                    default=True,
                                    type="boolean",
                                    label="Gps")])


class HelloViewTest(BaseWebTest):

    def test_returns_info_about_url_and_version(self):
        response = self.app.get('/')
        self.assertEqual(response.json['version'], VERSION)
        self.assertEqual(response.json['url'], 'http://localhost')
        self.assertEqual(response.json['daybed'], 'hello')

    def test_hello_uses_the_defined_http_scheme_if_defined(self):
        original_scheme = (self.app.app.registry.settings
                           .get('daybed.http_scheme'))
        try:
            self.app.app.registry.settings['daybed.http_scheme'] = 'https'
            response = self.app.get('/', headers=self.headers)
            self.assertTrue(
                response.json['url'].startswith('https'),
                '%s should start with https' % response.json['url'])
        finally:
            self.app.app.registry.settings['daybed.http_scheme'] =\
                original_scheme

    def test_authentication_headers_should_be_ignored(self):
        headers = self.headers.copy()
        headers['Authorization'] = 'Basic boom'
        self.app.get('/', headers=self.headers)

    def test_redirect_to_version(self):
        # We don't want the prefix to be automatically added for this test.
        original_request_class = self.app.RequestClass

        try:
            self.app.RequestClass = TestRequest  # Standard RequestClass.

            # GET on the hello view.
            response = self.app.get('/')
            self.assertEqual(response.status_int, 307)
            self.assertEqual(response.location,
                             'http://localhost/%s/' % API_VERSION)

            # GET on the fields view.
            response = self.app.get('/fields')
            self.assertEqual(response.status_int, 307)
            self.assertEqual(response.location,
                             'http://localhost/%s/fields' % API_VERSION)
        finally:
            self.app.RequestClass = original_request_class


class BasicAuthRegistrationTest(BaseWebTest):
    model_id = 'simple'

    @property
    def valid_definition(self):
        return {
            "title": "simple",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False}]
        }

    def test_unauthorized_if_no_credentials(self):
        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=self.headers)
        resp = self.app.get('/models/%s' % self.model_id,
                            status=401)
        self.assertIn('401', resp)

    def test_unauthorized_on_invalid_credentials(self):
        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=self.headers)

        auth = base64.b64encode(
            u'foo:bar'.encode('ascii')).strip().decode('ascii')

        resp = self.app.get('/models/%s' % self.model_id,
                            headers={
                                'Authorization': 'Basic {0}'.format(auth)
                            },
                            status=401)
        self.assertIn('401', resp)

    def test_forbidden_if_required_permission_missing(self):
        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=self.headers)
        self.app.patch_json('/models/%s/permissions' % self.model_id,
                            {self.credentials['id']: ["-ALL"]},
                            headers=self.headers)
        resp = self.app.get('/models/%s' % self.model_id,
                            headers=self.headers,
                            status=403)
        self.assertIn('403', resp)


class SporeTest(BaseWebTest):

    def test_spore_get(self):
        resp = self.app.get('/spore',
                            headers=self.headers, status=200)
        self.assertEqual(resp.json['name'], 'daybed')


class DefinitionViewsTest(BaseWebTest):

    def setUp(self):
        super(DefinitionViewsTest, self).setUp()
        model = copy.deepcopy(MODEL_DEFINITION)
        model['definition']['fields'].append({
            "name": "name",
            "type": "string"
        })
        model['permissions'] = {"system.Everyone": ["ALL"]}
        model['records'] = [{'name': 'Snowden', 'age': 31}]
        self.app.put_json('/models/test',
                          model,
                          headers=self.headers)

    def test_definition_retrieval(self):
        resp = self.app.get('/models/test/definition',
                            headers=self.headers)
        self.assertEqual(len(resp.json['fields']), 2)

    def test_definition_update_returns_new_definition(self):
        resp = self.app.put_json('/models/test/definition',
                                 MODEL_DEFINITION['definition'],
                                 headers=self.headers)
        self.assertEqual(len(resp.json['fields']), 1)

    def test_definition_update_must_be_valid(self):
        definition = MODEL_DEFINITION['definition'].copy()
        definition.pop('fields')
        self.app.put_json('/models/test/definition',
                          definition,
                          headers=self.headers, status=400)

    def test_definition_update_preserves_records(self):
        self.app.put_json('/models/test/definition',
                          MODEL_DEFINITION['definition'],
                          headers=self.headers)
        resp = self.app.get('/models/test/records',
                            headers=self.headers)
        self.assertEqual(len(resp.json['records']), 1)

    def test_definition_update_preserves_permissions(self):
        self.app.put_json('/models/test/definition',
                          MODEL_DEFINITION['definition'],
                          headers=self.headers)
        resp = self.app.get('/models/test/permissions',
                            headers=self.headers)
        self.assertIn('system.Everyone', resp.json)

    def test_model_creation_via_definition(self):
        self.app.put_json('/models/new/definition',
                          MODEL_DEFINITION['definition'],
                          headers=self.headers)
        resp = self.app.get('/models/new/records',
                            headers=self.headers)
        self.assertEqual(len(resp.json['records']), 0)


class ModelsViewsTest(BaseWebTest):

    def __init__(self, *args, **kwargs):
        self.maxDiff = None
        super(ModelsViewsTest, self).__init__(*args, **kwargs)

    def test_models(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.get('/models', headers=self.headers)
        self.assertDictEqual(resp.json, {
            "models": [
                {
                    "id": "test",
                    "title": "simple",
                    "description": "One optional field",
                }
            ]
        })

    def test_model_deletion(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.post_json('/models/test/records',
                                  MODEL_RECORD,
                                  headers=self.headers)
        record_id = resp.json['id']
        resp = self.app.delete('/models/test',
                               headers=self.headers)
        self.assertIn('name', resp.body.decode('utf-8'))
        self.assertRaises(RecordNotFound,
                          self.db.get_record, 'test', record_id)
        self.assertRaises(ModelNotFound, self.db.get_model_definition,
                          'test')

    def test_unknown_model_deletion_raises_404(self):
        self.app.delete('/models/unknown', {},
                        headers=self.headers,
                        status=404)

    def test_retrieve_whole_model(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.get('/models/test', {},
                            headers=self.headers)
        self.assertEqual(resp.json['records'], [])
        self.assertDictEqual(resp.json['permissions'],
                             {self.credentials['id']: MODEL_PERMISSIONS})

    def test_permissions_unknown_retrieval(self):
        resp = self.app.get('/models/test/permissions',
                            headers=self.headers, status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "location": "path",
                    "name": "test",
                    "description": "model not found"}],
                "status": "error"}))

    def test_permissions_retrieval(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.get('/models/test/permissions',
                            headers=self.headers)
        permissions = force_unicode(
            {self.credentials['id']: MODEL_PERMISSIONS}
        )
        self.assertDictEqual(resp.json, permissions)

    def test_patch_permissions(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)
        self.db.store_credentials('foo', {'id': 'alexis', 'key': 'bar'})
        self.db.store_credentials('foobar',  {'id': 'remy', 'key': 'bar'})

        resp = self.app.patch_json('/models/test/permissions',
                                   {"alexis": ["read_permissions"],
                                    "remy": ["update_permissions"]},
                                   headers=self.headers)
        permissions = force_unicode(
            {self.credentials['id']: MODEL_PERMISSIONS}
        )
        permissions[u"alexis"] = [u"read_permissions"]
        permissions[u"remy"] = [u"update_permissions"]
        self.assertDictEqual(resp.json, permissions)

    def test_put_permissions(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)
        self.db.store_credentials('foo', {'id': 'alexis', 'key': 'bar'})
        self.db.store_credentials('foobar', {'id': 'remy', 'key': 'bar'})

        resp = self.app.put_json('/models/test/permissions',
                                 {"alexis": ["read_permissions"],
                                  "remy": ["update_permissions"]},
                                 headers=self.headers)
        permissions = dict()
        permissions["alexis"] = ["read_permissions"]
        permissions["remy"] = ["update_permissions"]
        self.assertDictEqual(resp.json, force_unicode(permissions))

    def test_post_model_definition_with_records(self):
        model = MODEL_DEFINITION.copy()
        model['records'] = [MODEL_RECORD, MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']
        self.assertEquals(len(self.db.get_records(model_id)), 2)

    def test_put_model_definition_with_records(self):
        model = MODEL_DEFINITION.copy()
        model['records'] = [MODEL_RECORD, MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']

        model['records'] = [MODEL_RECORD]
        resp = self.app.put_json('/models/%s' % model_id, model,
                                 headers=self.headers)

        self.assertEquals(len(self.db.get_records(model_id)), 1)

    def test_post_model_definition_with_permissions(self):
        model = MODEL_DEFINITION.copy()
        model['permissions'] = {"Everyone": ["ALL"]}
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']

        definition = self.db.get_model_definition(model_id)
        self.assertEquals(definition, MODEL_DEFINITION['definition'])
        permissions = self.db.get_model_permissions(model_id)
        self.assertEquals(invert_permissions_matrix(permissions),
                          {self.credentials['id']: MODEL_PERMISSIONS,
                           u'system.Everyone': MODEL_PERMISSIONS})

    def test_put_model_definition_with_permissions(self):
        model = MODEL_DEFINITION.copy()
        model['permissions'] = {'Everyone': ['ALL']}
        self.app.put_json('/models/test', model,
                          headers=self.headers)

        permissions = self.db.get_model_permissions("test")
        self.assertEquals(invert_permissions_matrix(permissions),
                          {self.credentials['id']: MODEL_PERMISSIONS,
                           u'system.Everyone': MODEL_PERMISSIONS})

    def test_put_model_definition_new(self):
        model = MODEL_DEFINITION.copy()
        resp = self.app.put_json('/models/toto', model)
        self.assertIn("id", resp.json)

    def test_put_model_definition_update(self):
        model = MODEL_DEFINITION.copy()
        resp = self.app.put_json('/models/toto', model,
                                 headers=self.headers)
        self.assertIn("id", resp.json)
        self.assertEqual("toto", resp.json["id"])

        resp = self.app.put_json('/models/toto', model, status=401)

    def test_definition_creation_rejects_malformed_json(self):
        malformed_definition = '{"test":"toto", "titi": "tutu'
        resp = self.app.put('/models/test',
                            {'definition': malformed_definition},
                            headers=self.headers,
                            status=400)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))

    def test_delete_model(self):
        # 1. Test that the model and its records have been dropped
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.put_json('/models/test/records/123456',
                                 MODEL_RECORD, headers=self.headers)

        record = MODEL_RECORD.copy()
        record["id"] = resp.json["id"]

        self.db.store_credentials('foo', {'id': 'alexis', 'key': 'bar'})
        self.db.store_credentials('foobar', {'id': 'remy', 'key': 'bar'})

        permissions = {self.credentials['id']: ["delete_all_records",
                                                "delete_model"],
                       "alexis": ["read_permissions"],
                       "remy": ["update_permissions"]}

        resp = self.app.put_json(
            '/models/test/permissions',
            permissions,
            headers=self.headers)

        resp = self.app.delete('/models/test', headers=self.headers)

        # 2. Test that the returned data is right
        self.assertEqual(resp.json, force_unicode({
            'definition': MODEL_DEFINITION["definition"],
            'records': [record],
            'permissions': permissions}))


class RecordsViewsTest(BaseWebTest):

    def test_deserialized_value_is_stored(self):
        definition = copy.deepcopy(MODEL_DEFINITION)
        definition['definition']['fields'] = [{
            'name': 'updated',
            'type': 'date',
            'autonow': True}]
        self.app.put_json('/models/test', definition,
                          headers=self.headers)
        resp = self.app.post_json('/models/test/records', {},
                                  headers=self.headers)
        stored = self.db.get_record('test', resp.json['id'])
        self.assertIsNotNone(stored.get('updated'))

    def test_delete_model_records(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.post_json('/models/test/records', MODEL_RECORD,
                           headers=self.headers)
        resp = self.app.delete('/models/test/records',
                               headers=self.headers)
        self.assertIn("records", resp.json)
        self.assertTrue(len(resp.json["records"]), 1)
        self.assertIn("id", resp.json["records"][0])
        self.assertEqual(resp.json["records"][0]["age"], 42)

    def test_delete_unknown_model_records(self):
        resp = self.app.delete('/models/unknown/records', {},
                               headers=self.headers,
                               status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "location": "path",
                    "name": "unknown",
                    "description": "model not found"}],
                "status": "error"}))

    def test_unknown_model_raises_404(self):
        resp = self.app.get('/models/unknown/records', {},
                            headers=self.headers,
                            status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "location": "path",
                    "name": "unknown",
                    "description": "model not found"}],
                "status": "error"}))

    def test_unknown_model_records_creation(self):
        resp = self.app.post_json('/models/unknown/records', {},
                                  status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "description": "Unknown model unknown",
                    "location": "path",
                    "name": "modelname"
                }],
                "status": 'error'}
            ))

    def test_get_model_unknown(self):
        resp = self.app.get('/models/test',
                            headers=self.headers, status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "location": "path",
                    "name": "test",
                    "description": "model not found"}],
                "status": "error"}))

    def test_get_model_records(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.patch_json('/models/test/permissions',
                            {"Everyone": ["create_record", "read_own_records",
                                          "delete_own_records"]},
                            headers=self.headers)
        self.app.post_json('/models/test/records', MODEL_RECORD)
        self.app.post_json('/models/test/records', MODEL_RECORD2,
                           headers=self.headers)

        resp = self.app.get('/models/test/records',
                            headers=self.headers)
        self.assertEqual(len(resp.json["records"]), 2)

        resp = self.app.get('/models/test/records')
        self.assertEqual(len(resp.json["records"]), 1)

    def test_get_model_records_auto_json(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.patch_json('/models/test/permissions',
                            {"Everyone": ["create_record", "read_own_records",
                                          "delete_own_records"]},
                            headers=self.headers)
        self.app.post_json('/models/test/records', MODEL_RECORD)
        self.app.post_json('/models/test/records', MODEL_RECORD2,
                           headers=self.headers)

        resp = self.app.get('/models/test/records')
        self.assertEqual(len(resp.json["records"]), 1)

    def test_unknown_record_returns_404(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.get('/models/test/records/1234',
                            headers=self.headers, status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "location": "path",
                    "name": "1234",
                    "description": "record not found"}],
                "status": "error"}))

    def test_record_deletion(self):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.post_json('/models/test/records', MODEL_RECORD,
                                  headers=self.headers)
        record_id = resp.json['id']
        # Test 200
        resp = self.app.delete('/models/test/records/%s' % record_id,
                               headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))
        self.assertRaises(RecordNotFound, self.db.get_record,
                          'test', record_id)
        # Test 404
        resp = self.app.delete('/models/test/records/%s' % record_id,
                               headers=self.headers, status=404)

        self.assertDictEqual(resp.json, force_unicode({
            "errors": [{
                "location": "path",
                "name": record_id,
                "description": "record not found"}],
            "status": "error"}))

    def assertStartsWith(self, a, b):
        if not a.startswith(b):
            self.fail("'%s' doesn't startswith '%s'" % (a, b))


class CreateTokenViewTest(BaseWebTest):

    def setUp(self):
        super(CreateTokenViewTest, self).setUp()
        userpass = u'foolish:bar'.encode('ascii')
        self.auth = base64.b64encode(userpass).strip().decode('ascii')

    def test_post_token(self):
        response = self.app.post('/tokens', status=201)
        self.assertIn("token", response.json)
        self.assertTrue(len(response.json["token"]) == 64)
        self.assertIn("credentials", response.json)
        self.assertIn("id", response.json["credentials"])
        self.assertTrue(len(response.json["credentials"]["id"]) == 64)
        self.assertIn("key", response.json["credentials"])
        self.assertTrue(len(response.json["credentials"]["key"]) == 64)
        self.assertEqual("sha256", response.json["credentials"]["algorithm"])

    def test_post_token_with_basic_auth(self):
        response = self.app.post('/tokens', status=201, headers={
            'Authorization': 'Basic {0}'.format(self.auth)
        })
        credentials = response.json
        response = self.app.post('/tokens', status=200, headers={
            'Authorization': 'Basic {0}'.format(self.auth)
        })
        self.assertEqual(credentials, response.json)

    def test_post_token_with_token_authorization(self):
        response = self.app.post('/tokens', status=201, headers={
            'Authorization': 'Token {0}'.format(self.auth)
        })
        credentials = response.json
        response = self.app.post('/tokens', status=200, headers={
            'Authorization': 'Token {0}'.format(self.auth)
        })
        self.assertEqual(credentials, response.json)

    def test_post_token_is_not_the_same_for_basic_or_token(self):
        response = self.app.post('/tokens', status=201, headers={
            'Authorization': 'Token {0}'.format(self.auth)
        })
        credentials = response.json
        response = self.app.post('/tokens', status=201, headers={
            'Authorization': 'Basic {0}'.format(self.auth)
        })
        self.assertNotEqual(credentials, response.json)


class TokenViewTest(BaseWebTest):

    def test_unauthorized_if_not_authenticated(self):
        self.app.get('/token', status=401)

    def test_unauthorized_if_invalid_credentials(self):
        userpass = u'foolish:bar'.encode('ascii')
        auth = base64.b64encode(userpass).strip().decode('ascii')
        self.app.get('/token',
                     headers={
                         'Authorization': 'Basic {0}'.format(auth)
                     },
                     status=401)

    def test_return_credentials_if_authenticated(self):
        response = self.app.get('/token', headers=self.headers)
        self.assertEqual(len(response.json['token']), 64)
        self.assertDictEqual(response.json['credentials'],
                             self.credentials)


class SearchViewTest(BaseWebTest):

    def setUp(self):
        super(SearchViewTest, self).setUp()
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)

    def test_search_returns_200_if_query_is_correct(self):
        self.app.post('/models/test/search/', {'match_all': {}},
                      headers=self.headers,
                      status=200)
        self.app.get('/models/test/search/', {'match_all': {}},
                     headers=self.headers,
                     status=200)

    @mock.patch('elasticsearch.client.Elasticsearch.search')
    def test_search_supports_query_string_parameters(self, search_mock):
        search_mock.return_value = {}
        query = {'match_all': {}}
        self.app.post('/models/test/search/?size=100', query,
                      headers=self.headers,
                      status=200)
        search_mock.called_with(index='test', doc_type='test',
                                body=query, size=100)

    @mock.patch('elasticsearch.client.Elasticsearch.search')
    def test_search_ignores_unsupported_parameters(self, search_mock):
        search_mock.return_value = {}
        query = {'match_all': {}}
        self.app.get('/models/test/search/?size=1&from_=1&routing=a,b', query,
                     headers=self.headers,
                     status=200)
        search_mock.called_with(index='test', doc_type='test',
                                body=query, size=1, from_=1)

    def test_search_returns_404_if_model_unknown(self):
        self.app.get('/models/unknown/search/', {},
                     headers=self.headers,
                     status=404)

    @mock.patch('elasticsearch.client.Elasticsearch.search')
    def test_search_returns_502_if_elasticsearch_fails(self, search_mock):
        search_mock.side_effect = Exception('Not available')
        self.app.get('/models/test/search/', {},
                     headers=self.headers,
                     status=502)

    @mock.patch('elasticsearch.client.Elasticsearch.search')
    def test_search_returns_original_code_on_bad_request(self, search_mock):
        badrequest = elasticsearch.RequestError('400', 'error', {'foo': 'bar'})
        search_mock.side_effect = badrequest
        resp = self.app.get('/models/test/search/', {},
                            headers=self.headers,
                            status=400)
        self.assertEqual(resp.json['msg']['foo'], 'bar')

    def test_search_view_requires_permission(self):
        self.app.patch_json('/models/test/permissions',
                            {self.credentials['id']: ["-read_all_records"]},
                            headers=self.headers)
        self.app.get('/models/test/search/', {},
                     headers=self.headers,
                     status=403)


class CORSHeadersTest(BaseWebTest):

    def setUp(self):
        super(CORSHeadersTest, self).setUp()
        self.headers['Origin'] = 'notmyidea.org'

    def test_support_on_options_404(self):
        headers = self.headers.copy()
        headers['Access-Control-Request-Method'] = 'GET'
        response = self.app.options('/models/unknown/definition',
                                    headers=headers,
                                    status=200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_support_on_get_unknown_model(self):
        response = self.app.get('/models/unknown/definition',
                                headers=self.headers,
                                status=404)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_support_on_valid_definition(self):
        response = self.app.put_json('/models/test',
                                     MODEL_DEFINITION,
                                     headers=self.headers,
                                     status=200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_support_on_invalid_definition(self):
        definition = copy.deepcopy(MODEL_DEFINITION)
        definition['definition'].pop('fields')
        response = self.app.put_json('/models/test',
                                     definition,
                                     headers=self.headers,
                                     status=400)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_support_on_unauthorized(self):
        response = self.app.get('/token',
                                MODEL_DEFINITION,
                                headers={'Origin': 'notmyidea.org'},
                                status=401)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_support_on_forbidden(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers,
                          status=200)
        self.app.patch_json('/models/test/permissions',
                            {self.credentials['id']: ["-ALL"]},
                            headers=self.headers,
                            status=200)
        response = self.app.get('/models/test',
                                headers=self.headers,
                                status=403)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
