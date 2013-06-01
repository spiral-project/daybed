from daybed.tests.support import BaseWebTest
from daybed.schemas import registry


class DaybedViewsTest(BaseWebTest):
    """Daybed views tests.

    WIP #31 Migrate Lettuce tests to conventional unit tests
    """
    def test_fields_are_listed(self):
        response = self.app.get('/fields')
        fields = response.json
        names = [f.get('name') for f in fields]
        self.assertItemsEqual(names, registry.names)
        # String field has no parameters
        stringfield = [f for f in fields if f.get('name') == 'string'][0]
        self.assertIsNone(stringfield.get('parameters'))
        # Enum field describes list items type
        enumfield = [f for f in fields if f.get('name') == 'enum'][0]
        _type = enumfield['parameters'][0].get('items', {}).get('type')
        self.assertEqual('string', _type)
        # Point field describes GPS with default True
        pointfield = [f for f in fields if f.get('name') == 'point'][0]
        self.assertItemsEqual(pointfield['parameters'],
                              [dict(name="gps",
                                    default=True,
                                    type="boolean",
                                    description="Gps")])

    def test_unknown_model_data_creation(self):
        resp = self.app.post_json('/models/unknown/data', {},
                                  headers={'Content-Type': 'application/json'},
                                  status=404)
        self.assertIn('"status": "error"', resp.body)


class FunctionalTest(object):
    """These are the functional tests for daybed.

    The goal is to have them reproduce every possible scenario that we want to
    support in the application.

    The test suite is created in a way that each test is a different scenario.
    We reset the database each time we start a new test to avoid sharing
    context between tests.
    """

    model_id = None

    def __init__(self, *args, **kwargs):
        super(FunctionalTest, self).__init__(*args, **kwargs)
        self.definition_without_title = self.valid_definition.copy()
        self.definition_without_title.pop('title')
        self.malformed_definition = '{"test":"toto", "titi": "tutu'
        self.headers = {'Content-Type': 'application/json'}

    @property
    def valid_definition(self):
        raise NotImplementedError

    @property
    def valid_data(self):
        raise NotImplementedError

    @property
    def invalid_data(self):
        raise NotImplementedError

    def post_definition(self, data=None):
        if not data:
            data = self.valid_definition
        return self.app.post_json('/definitions/',
                                  data,
                                  headers=self.headers)

    def create_definition(self, data=None):
        if not data:
            data = self.valid_definition
        return self.app.put_json('/models/%s/definition' % self.model_id,
                                 data,
                                 headers=self.headers)

    def create_data(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/models/%s/data' % self.model_id,
                                  data,
                                  headers=self.headers)

    def create_data_resp(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/models/%s/data' % self.model_id,
                                  data,
                                  headers=self.headers)

    def test_post_normal_definition(self):
        resp = self.post_definition()
        self.assertIn('token', resp.body)
        self.assertIn('name', resp.body)

    def test_normal_definition_creation(self):
        self.create_definition()

    def test_malformed_definition_creation(self):
        resp = self.app.put_json('/models/%s/definition' % self.model_id,
                    self.definition_without_title,
                    headers=self.headers,
                    status=400)
        self.assertIn('"name": "title"', resp.body)

    def test_definition_creation_rejects_malformed_data(self):
        resp = self.app.put('/models/%s/definition' % self.model_id,
                    self.malformed_definition,
                    headers=self.headers,
                    status=400)
        self.assertIn('"status": "error"', resp.body)

    def test_definition_retrieval(self):
        self.create_definition()

        # Verify that the schema is the same
        resp = self.app.get('/models/%s/definition' % self.model_id,
                            headers=self.headers)
        self.assertEqual(resp.json, self.valid_definition)

    def test_definition_deletion_redirects(self):
        self.create_definition()
        self.app.delete('/models/%s/definition' % self.model_id, status=307)
        self.db.delete_model(self.model_id)

    def test_model_deletion(self):
        resp = self.create_definition()
        resp = self.create_data()
        data_item_id = resp.json['id']
        self.app.delete('/models/%s' % self.model_id)
        data_item = self.db.get_data_item(self.model_id, data_item_id)
        self.assertIsNone(data_item)
        model_definition = self.db.get_model_definition(self.model_id)
        self.assertIsNone(model_definition)

    def test_normal_data_creation(self):
        self.create_definition()

        # Put data against this definition
        resp = self.app.post_json('/models/%s/data' % self.model_id,
                                 self.valid_data,
                                 headers=self.headers)
        self.assertIn('id', resp.body)

    def test_invalid_data_validation(self):
        self.create_definition()

        # Try to put invalid data to this definition
        resp = self.app.post_json('/models/%s/data' % self.model_id,
                                  self.invalid_data,
                                  headers=self.headers,
                                  status=400)
        self.assertIn('"status": "error"', resp.body)

    def test_data_retrieval(self):
        self.create_definition()
        resp = self.create_data()

        # Put valid data against this definition
        self.assertIn('id', resp.body)

        data_item_id = resp.json['id']
        resp = self.app.get('/models/%s/data/%s' % (self.model_id,
                                                    data_item_id),
                            headers=self.headers)
        entry = self.valid_data.copy()
        # entry['id'] = str(data_item_id
        self.assertEqual(resp.json, entry)

    def test_data_item_update(self):
        self.create_definition()
        # Put data against this definition
        entry = self.valid_data.copy()
        resp = self.create_data(entry)
        data_item_id = resp.json['id']

        # Update this data
        self.update_data(entry)
        resp = self.app.put_json('/models/%s/data/%s' % (self.model_id,
                                                         data_item_id),
                                 entry,
                                 headers=self.headers)
        self.assertIn('id', resp.body)
        # Todo : Verify DB
        data_items = self.db.get_data_items(self.model_id)
        self.assertEqual(len(data_items), 1)

    def test_data_partial_update(self):
        self.create_definition()

        # Put data against this definition
        entry = self.valid_data.copy()
        resp = self.create_data(entry)
        data_item_id = resp.json['id']

        # Update this data
        self.update_data(entry)
        resp = self.app.patch_json('/models/%s/data/%s' % (self.model_id,
                                                           data_item_id),
                                   entry, headers=self.headers)
        self.assertIn('id', resp.body)

        # Check that we only have one value in the db (e.g that PATCH didn't
        # created a new data item)
        data_item = self.db.get_data_item(self.model_id, data_item_id)

        new_item = self.valid_data.copy()
        new_item.update(entry)
        self.assertEquals(data_item['data'], new_item)

    def test_data_deletion(self):
        self.create_definition()
        resp = self.create_data()
        data_item_id = resp.json['id']
        self.app.delete(str('/models/%s/data/%s' % (self.model_id,
                                                    data_item_id)))
        data_item = self.db.get_data_item(self.model_id, data_item_id)
        self.assertIsNone(data_item)

    def test_data_validation(self):
        self.create_definition()
        headers = self.headers.copy()
        headers['X-Daybed-Validate-Only'] = 'true'
        self.app.post_json('/models/%s/data' % self.model_id,
                           self.valid_data,
                           headers=headers, status=200)

        # no data should be added
        response = self.app.get('/models/%s/data' % self.model_id)
        self.assertEquals(0, len(response.json['data']))
        # of course, pushing weird data should tell what's wrong
        response = self.app.post_json('/models/%s/data' % self.model_id,
                                      self.invalid_data,
                                      headers=headers, status=400)
        # make sure the field name in cause is provided
        self.assertIn('errors', response.json)
        errors = response.json['errors']
        self.assertTrue(len(errors) > 0)
        self.assertIn('name', errors[0])
        self.assertNotEquals('', errors[0]['name'])

    def test_cors_support_on_404(self):
        response = self.app.get('/models/unknown/definition',
                                headers={'Origin': 'notmyidea.org'},
                                status=404)
        self.assertIn('Access-Control-Allow-Origin', response.headers)


class SimpleModelTest(FunctionalTest, BaseWebTest):

    model_id = 'simple'

    @property
    def valid_definition(self):
        return {
            "title": "simple",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False}]
        }

    @property
    def valid_data(self):
        return {}

    @property
    def invalid_data(self):
        return {'age': 'abc'}

    def update_data(self, entry):
        entry.pop('age', 0)


class TodoModelTest(FunctionalTest, BaseWebTest):

    model_id = 'todo'

    @property
    def valid_definition(self):
        return {
            "title": "todo",
            "description": "A list of my stuff to do",
            "fields": [
                {
                    "name": "item",
                    "type": "string",
                    "description": "The item"
                },
                {
                    "name": "status",
                    "type": "enum",
                    "choices": [
                        "done",
                        "todo"
                    ],
                    "description": "is it done or not"
                }
            ]
        }

    @property
    def valid_data(self):
        return {'item': 'My task', 'status': 'todo'}

    @property
    def invalid_data(self):
        return {'item': 'Invalid task', 'status': 'yay'}

    def update_data(self, entry):
        entry['status'] = 'done'


class TimestampedModelTest(FunctionalTest, BaseWebTest):

    model_id = 'timestamped'

    @property
    def valid_definition(self):
        return {
            "title": "timestamped",
            "description": "Playing with date fields",
            "fields": [
                {
                    "name": "creation",
                    "type": "date",
                    "description": "created on"
                },
                {
                    "name": "modified",
                    "type": "datetime",
                    "description": "modified on",
                    "auto_now": True
                },
            ]
        }

    @property
    def valid_data(self):
        return {'creation': '2012-04-15', 'modified': ''}

    @property
    def invalid_data(self):
        return {'creation': '15-04-2012', 'modified': ''}

    def update_data(self, entry):
        entry['creation'] = '2013-05-30'
        entry['modified'] = ''


class MushroomsModelTest(FunctionalTest, BaseWebTest):

    model_id = 'mushroom_spots'

    @property
    def valid_definition(self):
        return {
            "title": "Mushroom Spots",
            "description": "Where are they ?",
            "fields": [
                {
                    "name": "mushroom",
                    "type": "string",
                    "description": "Species"
                },
                {
                    "name": "location",
                    "type": "polygon",
                    "description": "Area spotted"
                }
            ]
        }

    @property
    def valid_data(self):
        return {'mushroom': 'Boletus',
                'location': [[[0, 0], [0, 1], [1, 1]]]}

    @property
    def invalid_data(self):
        return {'mushroom': 'Boletus',
                'location': [[0, 0], [0, 1]]}

    def update_data(self, entry):
        entry['location'] = [[[0, 0], [0, 2], [2, 2]],
                             [[0.5, 0.5], [0.5, 1], [1, 1]]]


class CityModelTest(FunctionalTest, BaseWebTest):

    model_id = 'city'

    @property
    def valid_definition(self):
        return {
            "title": "capitals",
            "description": "in the world",
            "fields": [
                {
                    "name": "name",
                    "type": "string",
                    "description": "Administrative"
                },
                {
                    "name": "location",
                    "type": "point",
                    "description": "(x,y,z)"
                }
            ]
        }

    @property
    def valid_data(self):
        return {'name': 'La Paz', 'location': [-16.5, -68.15, 3500]}

    @property
    def invalid_data(self):
        return {'name': 'La Paz', 'location': [2012, 12, 21]}

    def update_data(self, entry):
        entry['name'] = 'Sucre'
        entry['location'] = [-19.0, -65.2, 500]


class EuclideModelTest(FunctionalTest, BaseWebTest):

    model_id = 'position'

    @property
    def valid_definition(self):
        return {
            "title": "positions",
            "description": "euclidean",
            "fields": [
                {
                    "name": "location",
                    "type": "point",
                    "description": "(x,y)",
                    "gps": False
                }
            ]
        }

    @property
    def valid_data(self):
        return {'location': [2012, 3042]}

    @property
    def invalid_data(self):
        return {'location': [0]}

    def update_data(self, entry):
        entry['location'] = [21, 12, 2012]
