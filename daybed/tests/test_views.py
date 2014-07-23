from daybed import __version__ as VERSION
from daybed.backends.exceptions import RecordNotFound, ModelNotFound
from daybed.tests.support import BaseWebTest, force_unicode
from daybed.schemas import registry


SIMPLE_MODEL_DEFINITION = {
    'definition': {
        "title": "simple",
        "description": "One optional field",
        "fields": [{"name": "age",
                    "type": "int",
                    "required": False}]
    }
}

SIMPLE_MODEL_RECORD = {'age': 42}


class DaybedViewsTest(BaseWebTest):

    def __init__(self, *args, **kwargs):
        super(DaybedViewsTest, self).__init__(*args, **kwargs)
        if not hasattr(self, 'assertCountEqual'):
            self.assertCountEqual = self.assertItemsEqual

    def test_hello(self):
        response = self.app.get('/', headers=self.headers)
        self.assertDictEqual({'version': VERSION,
                              'url': 'http://localhost',
                              'daybed': 'hello'}, response.json)

    def test_persona(self):
        self.app.get('/persona', headers=self.headers)

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

    # XXX: We don't create automatically the user on first login attempt.
    # def test_basic_auth_user_creation(self):
    #     auth_password = base64.b64encode(
    #         u'arthur:foo'.encode('ascii')).strip().decode('ascii')
    #     headers = {
    #         'Content-Type': 'application/json',
    #         'Authorization': 'Basic {0}'.format(auth_password),
    #     }
    #
    #     self.app.put_json('/models/%s' % self.model_id,
    #                       {'definition': self.valid_definition},
    #                       headers=headers)
    #
    #     try:
    #         self.db.get_user('arthur')
    #     except UserNotFound:
    #         self.fail("BasicAuth didn't create the user arthur.")

    def test_forbidden(self):
        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=self.headers)
        resp = self.app.get('/models/%s' % self.model_id,
                            headers={'Content-Type': 'application/json'},
                            status=401)
        self.assertIn('401', resp)


class SporeTest(BaseWebTest):

    def test_spore_get(self):
        resp = self.app.get('/spore',
                            headers=self.headers, status=200)
        self.assertEqual(resp.json['name'], 'daybed')


class ModelsViewsTest(BaseWebTest):

    def test_model_deletion(self):
        self.app.put_json('/models/test', SIMPLE_MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.post_json('/models/test/records',
                                  SIMPLE_MODEL_RECORD,
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

    def test_retrieve_whole_model_definition(self):
        self.app.put_json('/models/test', SIMPLE_MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.get('/models/test', {},
                            headers=self.headers)
        self.assertEqual(resp.json['records'], [])
        self.assertDictEqual(resp.json['acls'], {
            'read_acls': ['admin'],
            'update_definition': ['admin'],
            'delete_all_records': ['admin'],
            'read_all_records': ['admin'],
            'update_my_record': ['admin'],
            'read_my_record': ['admin'],
            'read_definition': ['admin'],
            'delete_my_record': ['admin'],
            'update_acls': ['admin'],
            'create_record': ['admin'],
            'update_all_records': ['admin'],
            'delete_model': ['admin']
        })

    def test_post_model_definition_without_definition(self):
        self.app.post_json('/models', {}, headers=self.headers, status=400)

    def test_post_model_definition_without_records(self):
        resp = self.app.post_json('/models',
                                  SIMPLE_MODEL_DEFINITION,
                                  headers=self.headers)
        model_id = resp.json['id']

        definition = self.db.get_model_definition(model_id)
        self.assertEquals(definition, SIMPLE_MODEL_DEFINITION['definition'])

    def test_cors_support_on_404(self):
        response = self.app.get('/models/unknown/definition',
                                headers={'Origin': 'notmyidea.org'},
                                status=404)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_definition_retrieval(self):
        self.app.put_json('/models/test',
                          SIMPLE_MODEL_DEFINITION,
                          headers=self.headers)
        # Verify that the schema is the same
        resp = self.app.get('/models/test/definition',
                            headers=self.headers)
        definition = force_unicode(SIMPLE_MODEL_DEFINITION['definition'])
        self.assertDictEqual(resp.json, definition)

    def test_post_model_definition_with_records(self):
        model = SIMPLE_MODEL_DEFINITION.copy()
        model['records'] = [SIMPLE_MODEL_RECORD, SIMPLE_MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']
        self.assertEquals(len(self.db.get_records(model_id)), 2)

    def test_put_model_definition_without_records(self):
        model = SIMPLE_MODEL_DEFINITION.copy()
        model['records'] = [SIMPLE_MODEL_RECORD, SIMPLE_MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']

        model.pop('records')
        resp = self.app.put_json('/models/%s' % model_id, model,
                                 headers=self.headers)

        self.assertEquals(len(self.db.get_records(model_id)), 0)

    def test_put_model_definition_with_records(self):
        model = SIMPLE_MODEL_DEFINITION.copy()
        model['records'] = [SIMPLE_MODEL_RECORD, SIMPLE_MODEL_RECORD]
        resp = self.app.post_json('/models', model,
                                  headers=self.headers)
        model_id = resp.json['id']

        model['records'] = [SIMPLE_MODEL_RECORD]
        resp = self.app.put_json('/models/%s' % model_id, model,
                                 headers=self.headers)

        self.assertEquals(len(self.db.get_records(model_id)), 1)

    def test_malformed_definition_creation(self):
        definition_without_title = SIMPLE_MODEL_DEFINITION['definition'].copy()
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


class RecordsViewsTest(BaseWebTest):

    def test_delete_model_records(self):
        self.app.put_json('/models/test', SIMPLE_MODEL_DEFINITION,
                          headers=self.headers)
        self.app.delete('/models/test/records', {},
                        headers=self.headers)

    def test_delete_unknown_model_records(self):
        self.app.delete('/models/unknown/records', {},
                        headers=self.headers,
                        status=404)

    def test_unknown_model_raises_404(self):
        self.app.get('/models/unknown/records', {},
                     headers=self.headers,
                     status=404)

    def test_unknown_model_records_creation(self):
        resp = self.app.post_json('/models/unknown/records', {},
                                  headers={'Content-Type': 'application/json'},
                                  status=404)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))

    def test_unknown_record_returns_404(self):
        self.app.put_json('/models/test', SIMPLE_MODEL_DEFINITION,
                          headers=self.headers)
        self.app.get('/models/test/records/1234',
                     headers=self.headers, status=404)

    def test_record_deletion(self):
        self.app.put_json('/models/test', SIMPLE_MODEL_DEFINITION,
                          headers=self.headers)
        resp = self.app.post_json('/models/test/records', SIMPLE_MODEL_RECORD,
                                  headers=self.headers)
        record_id = resp.json['id']
        # Test 200
        resp = self.app.delete('/models/test/records/%s' % record_id,
                               headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))
        self.assertRaises(RecordNotFound, self.db.get_record,
                          'test', record_id)
        # Test 404
        self.app.delete('/models/test/records/%s' % record_id,
                        headers=self.headers, status=404)
