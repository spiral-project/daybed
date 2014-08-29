import base64

import mock
from pyramid.security import Authenticated, Everyone

from daybed import __version__ as VERSION
from daybed.permissions import PERMISSIONS_SET
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
                            headers={'Content-Type': 'application/json'},
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
                                'Content-Type': 'application/json',
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

    def test_post_model_definition_without_definition(self):
        self.app.post_json('/models', {}, headers=self.headers, status=400)

    def test_post_model_definition_without_records(self):
        resp = self.app.post_json('/models',
                                  MODEL_DEFINITION,
                                  headers=self.headers)
        model_id = resp.json['id']

        definition = self.db.get_model_definition(model_id)
        self.assertEquals(definition, MODEL_DEFINITION['definition'])

    def test_cors_support_on_404(self):
        headers = self.headers.copy()
        headers['Origin'] = 'notmyidea.org'
        response = self.app.get('/models/unknown/definition',
                                headers=headers,
                                status=404)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

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

    def test_patch_permissions_add(self):
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

    def test_patch_permissions_remove(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json(
            '/models/test/permissions',
            {self.credentials['id']: ["-read_permissions",
                                      "-update_permissions"]},
            headers=self.headers)
        permissions = force_unicode(
            {self.credentials['id']: MODEL_PERMISSIONS}
        )
        permissions[self.credentials['id']].remove("read_permissions")
        permissions[self.credentials['id']].remove("update_permissions")
        self.assertDictEqual(resp.json, permissions)

    def test_patch_permissions_add_all(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)
        self.db.store_credentials('foo', {'id': 'alexis', 'key': 'bar'})

        resp = self.app.patch_json('/models/test/permissions',
                                   {"alexis": ["ALL"]},
                                   headers=self.headers)
        permissions = force_unicode(
            {self.credentials['id']: MODEL_PERMISSIONS}
        )
        permissions[u"alexis"] = sorted(PERMISSIONS_SET)
        self.assertDictEqual(resp.json, permissions)

    def test_patch_permissions_add_system_principals(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json(
            '/models/test/permissions',
            {Everyone: ["read_definition"],
             Authenticated: ["read_definition", "read_permissions"]},
            headers=self.headers
        )
        permissions = force_unicode(
            {self.credentials['id']: MODEL_PERMISSIONS}
        )
        permissions[Authenticated] = ["read_definition", "read_permissions"]
        permissions[Everyone] = ["read_definition"]
        self.assertDictEqual(resp.json, permissions)

    def test_patch_permissions_add_shortcuts_principals(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json(
            '/models/test/permissions',
            {"Everyone": ["read_definition"],
             "Authenticated": ["read_definition", "read_permissions"]},
            headers=self.headers
        )
        permissions = force_unicode(
            {self.credentials['id']: MODEL_PERMISSIONS}
        )
        permissions[Authenticated] = ["read_definition", "read_permissions"]
        permissions[Everyone] = ["read_definition"]
        self.assertDictEqual(resp.json, permissions)

    def test_patch_permissions_remove_all(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json('/models/test/permissions',
                                   {self.credentials['id']: ["-all"]},
                                   headers=self.headers)
        self.assertDictEqual(resp.json, {})

    def test_patch_permissions_add_unknown(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json('/models/test/permissions',
                                   {"alexis": ["read_permissions"]},
                                   headers=self.headers,
                                   status=400)
        self.assertDictEqual(resp.json, force_unicode({
            "status": "error",
            "errors": [
                {"location": "body", "name": "alexis",
                 "description": "Credentials id couldn't be found."}
            ]
        }))

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

    def test_put_permissions_wrong_identifier(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.put_json('/models/test/permissions',
                                 {"alexis": ["read_permissions"]},
                                 headers=self.headers,
                                 status=400)

        self.assertDictEqual(resp.json, force_unicode({
            "status": "error",
            "errors": [
                {"location": "body", "name": "alexis",
                 "description": "Credentials id couldn't be found."}
            ]
        }))

    def test_put_permissions_wrong_perm(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.put_json('/models/test/permissions',
                                 {"Everyone": ["foo", "read_permissions"]},
                                 headers=self.headers,
                                 status=400)

        self.assertDictEqual(resp.json, force_unicode({
            "status": "error",
            "errors": [
                {"location": "body", "name": "Everyone",
                 "description": "Invalid permissions: foo"}
            ]
        }))

    def test_definition_retrieval(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.get('/models/test/definition',
                            headers=self.headers)
        definition = force_unicode(MODEL_DEFINITION['definition'])
        self.assertDictEqual(resp.json, definition)

    def test_post_model_definition_with_records(self):
        model = MODEL_DEFINITION.copy()
        model['records'] = [MODEL_RECORD, MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']
        self.assertEquals(len(self.db.get_records(model_id)), 2)

    def test_put_model_definition_without_records(self):
        model = MODEL_DEFINITION.copy()
        model['records'] = [MODEL_RECORD, MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']

        model.pop('records')
        resp = self.app.put_json('/models/%s' % model_id, model,
                                 headers=self.headers)

        self.assertEquals(len(self.db.get_records(model_id)), 0)

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

    def test_malformed_definition_creation(self):
        definition_without_title = MODEL_DEFINITION['definition'].copy()
        definition_without_title.pop('title')
        resp = self.app.put_json('/models/test',
                                 {'definition': definition_without_title},
                                 headers=self.headers,
                                 status=400)
        self.assertIn('"name": "title"', resp.body.decode('utf-8'))

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
                                  headers={'Content-Type': 'application/json'},
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

        resp = self.app.get('/models/test/records', headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
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
        self.assertEqual(resp.headers['Content-Type'],
                         "application/json; charset=UTF-8")
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


class TokenViewTest(BaseWebTest):

    def test_unauthorized_if_not_authenticated(self):
        self.app.get('/token', status=401)

    def test_denied_if_invalid_credentials(self):
        auth = base64.b64encode(
                    u'foolish:bar'.encode('ascii')).strip().decode('ascii')
        self.app.get('/token',
                     headers={
                         'Content-Type': 'application/json',
                         'Authorization': 'Basic {0}'.format(auth)
                     },
                     status=403)

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
        self.app.get('/models/test/search/', {'match_all': {}},
                     headers=self.headers,
                     status=200)

    @mock.patch('elasticsearch.client.Elasticsearch.search')
    def test_search_supports_query_string_parameters(self, search_mock):
        search_mock.return_value = {}
        query = {'match_all': {}}
        self.app.get('/models/test/search/?size=100', query,
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

    def test_search_view_requires_permission(self):
        self.app.patch_json('/models/test/permissions',
                            {self.credentials['id']: ["-read_all_records"]},
                            headers=self.headers)
        self.app.get('/models/test/search/', {},
                     headers=self.headers,
                     status=403)
