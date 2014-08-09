import base64
from pyramid.security import Authenticated, Everyone
from daybed import __version__ as VERSION
from daybed.acl import PERMISSIONS_SET
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

MODEL_ACLS = {
    'admin': [
        'create_record',
        'delete_all_records',
        'delete_model',
        'delete_own_records',
        'read_acls',
        'read_all_records',
        'read_definition',
        'read_own_records',
        'update_acls',
        'update_all_records',
        'update_definition',
        'update_own_records',
    ]
}

MODEL_RECORD = {'age': 42}
MODEL_RECORD2 = {'age': 25}


class DaybedViewsTest(BaseWebTest):

    def __init__(self, *args, **kwargs):
        super(DaybedViewsTest, self).__init__(*args, **kwargs)
        if not hasattr(self, 'assertCountEqual'):
            self.assertCountEqual = self.assertItemsEqual

    def test_hello(self):
        response = self.app.get('/', headers=self.headers)
        self.assertDictEqual({'version': VERSION,
                              'url': 'http://localhost',
                              'token': 'admin',
                              'daybed': 'hello'}, response.json)

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


class BasicAuthRegistrationTest(BaseWebTest):
    model_id = 'simple'

    @property
    def valid_definition(self):
        return {
            "title": "simple",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False}]
        }

    def test_unauthorized(self):
        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=self.headers)
        resp = self.app.get('/models/%s' % self.model_id,
                            headers={'Content-Type': 'application/json'},
                            status=401)
        self.assertIn('401', resp)

    def test_unauthorized_token(self):
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

    def test_forbidden(self):
        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=self.headers)
        self.app.patch_json('/models/%s/permissions' % self.model_id,
                            {"admin": ["-ALL"]},
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
        self.assertDictEqual(resp.json['acls'], MODEL_ACLS)

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
        response = self.app.get('/models/unknown/definition',
                                headers={'Origin': 'notmyidea.org'},
                                status=404)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_acls_unknown_retrieval(self):
        resp = self.app.get('/models/test/permissions',
                            headers=self.headers, status=404)
        self.assertDictEqual(
            resp.json, force_unicode({
                "errors": [{
                    "location": "path",
                    "name": "test",
                    "description": "model not found"}],
                "status": "error"}))

    def test_acls_retrieval(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.get('/models/test/permissions',
                            headers=self.headers)
        acls = force_unicode(MODEL_ACLS)
        self.assertDictEqual(resp.json, acls)

    def test_patch_acls_add(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)
        self.db.add_token('alexis', 'bar')
        self.db.add_token('remy', 'foobar')

        resp = self.app.patch_json('/models/test/permissions',
                                   {"alexis": ["read_acls"],
                                    "remy": ["update_acls"]},
                                   headers=self.headers)
        acls = force_unicode(MODEL_ACLS)
        acls[u"alexis"] = [u"read_acls"]
        acls[u"remy"] = [u"update_acls"]
        self.assertDictEqual(resp.json, acls)

    def test_patch_acls_remove(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json('/models/test/permissions',
                                   {"admin": ["-read_acls", "-update_acls"]},
                                   headers=self.headers)
        acls = force_unicode(MODEL_ACLS)
        acls[u"admin"].remove("read_acls")
        acls[u"admin"].remove("update_acls")
        self.assertDictEqual(resp.json, acls)

    def test_patch_acls_add_all(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)
        self.db.add_token('alexis', 'bar')

        resp = self.app.patch_json('/models/test/permissions',
                                   {"alexis": ["ALL"]},
                                   headers=self.headers)
        acls = force_unicode(MODEL_ACLS)
        acls[u"alexis"] = sorted(PERMISSIONS_SET)
        self.assertDictEqual(resp.json, acls)

    def test_patch_acls_add_system_principals(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json(
            '/models/test/permissions',
            {Everyone: ["read_definition"],
             Authenticated: ["read_definition", "read_acls"]},
            headers=self.headers
        )
        acls = force_unicode(MODEL_ACLS)
        acls[Authenticated] = ["read_acls", "read_definition"]
        acls[Everyone] = ["read_definition"]
        self.assertDictEqual(resp.json, acls)

    def test_patch_acls_add_shortcuts_principals(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json(
            '/models/test/permissions',
            {"Everyone": ["read_definition"],
             "Authenticated": ["read_definition", "read_acls"]},
            headers=self.headers
        )
        acls = force_unicode(MODEL_ACLS)
        acls[Authenticated] = ["read_acls", "read_definition"]
        acls[Everyone] = ["read_definition"]
        self.assertDictEqual(resp.json, acls)

    def test_patch_acls_remove_all(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json('/models/test/permissions',
                                   {"admin": ["-all"]},
                                   headers=self.headers)
        self.assertDictEqual(resp.json, {})

    def test_patch_acls_add_unknown(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.patch_json('/models/test/permissions',
                                   {"alexis": ["read_acls"]},
                                   headers=self.headers,
                                   status=400)
        self.assertDictEqual(resp.json, force_unicode({
            "status": "error",
            "errors": [
                {"location": "body", "name": "alexis",
                 "description": "Token couldn't be found."}
            ]
        }))

    def test_put_acls(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)
        self.db.add_token('alexis', 'bar')
        self.db.add_token('remy', 'foobar')

        resp = self.app.put_json('/models/test/permissions',
                                 {"alexis": ["read_acls"],
                                  "remy": ["update_acls"]},
                                 headers=self.headers)
        acls = dict()
        acls["alexis"] = ["read_acls"]
        acls["remy"] = ["update_acls"]
        self.assertDictEqual(resp.json, force_unicode(acls))

    def test_put_acls_wrong_token(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.put_json('/models/test/permissions',
                                 {"alexis": ["read_acls"]},
                                 headers=self.headers,
                                 status=400)

        self.assertDictEqual(resp.json, force_unicode({
            "status": "error",
            "errors": [
                {"location": "body", "name": "alexis",
                 "description": "Token couldn't be found."}
            ]
        }))

    def test_put_acls_wrong_perm(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        resp = self.app.put_json('/models/test/permissions',
                                 {"Everyone": ["foo", "read_acls"]},
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

    def test_definition_retrieval_as_json_schema(self):
        self.app.put_json('/models/test',
                          MODEL_DEFINITION,
                          headers=self.headers)

        self.headers['Accept'] = 'application/schema+json'

        resp = self.app.get('/models/test/definition',
                            headers=self.headers)

        self.assertDictEqual(resp.json, {
            '$schema': 'http://json-schema.org/schema#',
            'title': 'simple',
            'description': u'One optional field',
            'type': 'object',
            'properties': {
                'age': {
                    'description': 'age',
                    'type': 'integer',
                }
            },
            'required': []
        })

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

        self.db.add_token('alexis', 'bar')
        self.db.add_token('remy', 'foobar')

        acls = {"admin": ["delete_all_records", "delete_model"],
                "alexis": ["read_acls"],
                "remy": ["update_acls"]}

        resp = self.app.put_json(
            '/models/test/permissions',
            acls,
            headers=self.headers)

        resp = self.app.delete('/models/test', headers=self.headers)

        # 2. Test that the returned data is right
        self.assertEqual(resp.json, force_unicode({
            'definition': MODEL_DEFINITION["definition"],
            'records': [record],
            'acls': acls}))


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


class TokensViewsTest(BaseWebTest):

    def test_post_token(self):
        response = self.app.post('/tokens', status=201)
        self.assertIn("sessionToken", response.json)
        self.assertTrue(len(response.json["sessionToken"]) == 64)
        self.assertIn("credentials", response.json)
        self.assertIn("id", response.json["credentials"])
        self.assertTrue(len(response.json["credentials"]["id"]) == 64)
        self.assertIn("key", response.json["credentials"])
        self.assertTrue(len(response.json["credentials"]["key"]) == 64)
        self.assertEqual("sha256", response.json["credentials"]["algorithm"])
