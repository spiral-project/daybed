import base64


from daybed import __version__ as VERSION
from daybed.backends.exceptions import UserNotFound
from daybed.tests.support import BaseWebTest
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

    def test_basic_auth_user_creation(self):
        auth_password = base64.b64encode(
            u'arthur:foo'.encode('ascii')).strip().decode('ascii')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic {0}'.format(auth_password),
        }

        self.app.put_json('/models/%s' % self.model_id,
                          {'definition': self.valid_definition},
                          headers=headers)

        try:
            self.db.get_user('arthur')
        except UserNotFound:
            self.fail("BasicAuth didn't create the user arthur.")

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

    def test_unknown_model_deletion_raises_404(self):
        self.app.delete('/models/unknown', {},
                        headers=self.headers,
                        status=404)

    def test_retrieve_whole_model_definition(self):
        model = SIMPLE_MODEL_DEFINITION.copy()
        self.app.put_json('/models/test', model,
                          headers=self.headers)
        resp = self.app.get('/models/test', {},
                            headers=self.headers)
        self.assertEqual(resp.json['records'], [])
        self.assertDictEqual(resp.json['acls'], {
            "read_definition": ["Remy", "Alexis"]
        })


class RecordsViewsTest(BaseWebTest):

    def test_delete_model_records(self):
        model = SIMPLE_MODEL_DEFINITION.copy()
        self.app.put_json('/models/test', model,
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

    def test_unknown_model_data_creation(self):
        resp = self.app.post_json('/models/unknown/records', {},
                                  headers={'Content-Type': 'application/json'},
                                  status=404)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))
