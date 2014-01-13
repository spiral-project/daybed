import json
from uuid import uuid4
import base64

from daybed import __version__ as VERSION
from daybed.backends.exceptions import UserNotFound
from daybed.tests.support import BaseWebTest
from daybed.schemas import registry
from daybed.acl import USER_AUTHENTICATED


class DaybedViewsTest(BaseWebTest):

    def __init__(self, *args, **kwargs):
        super(DaybedViewsTest, self).__init__(*args, **kwargs)
        if not hasattr(self, 'assertCountEqual'):
            self.assertCountEqual = self.assertItemsEqual

    def test_hello(self):
        response = self.app.get('/', headers=self.headers)
        self.assertDictEqual({'version': VERSION,
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
                                    description="Gps")])

    def test_unknown_model_data_creation(self):
        resp = self.app.post_json('/models/unknown/records', {},
                                  headers={'Content-Type': 'application/json'},
                                  status=404)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))


class BasicAuthRegistrationTest(BaseWebTest):
    model_id = 'simple'

    @property
    def valid_definition(self):
        return {
            "title": "simple",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False,
                        "description": ""}]
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


class PolicyTest(BaseWebTest):

    def test_policy_put_get_delete_ok(self):
        policy_id = 'read-only%s' % uuid4()
        policy = {'role:admins': 0xFFFF,
                  USER_AUTHENTICATED: 0x4400}

        # Test Create
        self.app.put_json('/policies/%s' % policy_id,
                          policy,
                          headers=self.headers, status=200)

        # Test Get
        resp = self.app.get('/policies/%s' % policy_id,
                            headers=self.headers, status=200)
        self.assertDictEqual(json.loads(resp.body.decode('utf-8')), policy)

        # Test Create another time with the same name
        self.app.put_json('/policies/%s' % policy_id,
                          policy,
                          headers=self.headers, status=409)

        # Test Create a definition with it
        model = {'definition': {"title": "simple",
                                "description": "One optional field",
                                "fields": [{"name": "age", "type": "int",
                                            "required": False}]
                                },
                 'policy_id': policy_id}

        self.app.put_json('/models/test', model,
                          headers=self.headers, status=200)

        # Test Delete when used
        self.app.delete('/policies/%s' % policy_id,
                        headers=self.headers, status=403)

        # Delete the model
        self.app.delete('/models/test',
                        headers=self.headers, status=200)

        # Test Delete when not used
        self.app.delete('/policies/%s' % policy_id,
                        headers=self.headers, status=200)

        self.app.get('/policies/%s' % policy_id,
                     headers=self.headers, status=404)

    def test_policy_put_wrong(self):
        policy_id = 'read-only%s' % uuid4()
        policy = {'role:admins': 'toto'}
        self.app.put_json('/policies/%s' % policy_id,
                          policy,
                          headers=self.headers, status=400)

    def test_policies_list(self):
        resp = self.app.get('/policies', headers=self.headers, status=200)
        self.assertDictEqual(
            json.loads(resp.body.decode('utf-8')),
            {"policies": ["admin-only", "anonymous", "read-only"]})


class SporeTest(BaseWebTest):

    def test_spore_get(self):
        resp = self.app.get('/spore',
                            headers=self.headers, status=200)
        self.assertEqual(resp.json['name'], 'daybed')
