# -*- coding: utf-8 -*-
import six

from daybed.backends.exceptions import RecordNotFound, ModelNotFound
from daybed.tests.support import BaseWebTest, force_unicode


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

        if not hasattr(self, 'assertCountEqual'):
            self.assertCountEqual = self.assertItemsEqual

    @property
    def valid_definition(self):
        raise NotImplementedError

    @property
    def valid_data(self):
        raise NotImplementedError

    @property
    def invalid_data(self):
        raise NotImplementedError

    def test_post_model_definition_without_definition(self):
        self.app.post_json('/models', {}, headers=self.headers, status=400)

    def test_post_model_definition_without_data(self):
        resp = self.app.post_json('/models',
                                  {'definition': self.valid_definition},
                                  headers=self.headers)
        model_id = resp.json['id']

        definition = self.db.get_model_definition(model_id)
        self.assertEquals(definition, self.valid_definition)

    def test_post_model_definition_wrong_policy(self):
        self.app.post_json('/models',
                           {'definition': self.valid_definition,
                            'policy_id': 'unknown'},
                           headers=self.headers,
                           status=400)

    def test_post_model_definition_with_data(self):
        resp = self.app.post_json('/models',
                                  {'definition': self.valid_definition,
                                   'records': [self.valid_data,
                                               self.valid_data]},
                                  headers=self.headers)
        model_id = resp.json['id']
        self.assertEquals(len(self.db.get_records(model_id)), 2)

    def test_put_model_definition_without_data(self):
        resp = self.app.post_json('/models',
                                  {'definition': self.valid_definition,
                                   'records': [self.valid_data,
                                               self.valid_data]},
                                  headers=self.headers)
        model_id = resp.json['id']

        resp = self.app.put_json('/models/%s' % model_id,
                                 {'definition': self.valid_definition},
                                 headers=self.headers)

        self.assertEquals(len(self.db.get_records(model_id)), 0)

    def test_put_model_definition_with_data(self):
        resp = self.app.post_json('/models',
                                  {'definition': self.valid_definition,
                                   'records': [self.valid_data,
                                               self.valid_data]},
                                  headers=self.headers)
        model_id = resp.json['id']

        resp = self.app.put_json('/models/%s' % model_id,
                                 {'definition': self.valid_definition,
                                  'records': [self.valid_data]},
                                 headers=self.headers)

        self.assertEquals(len(self.db.get_records(model_id)), 1)

    def create_definition(self, data=None):
        if not data:
            data = self.valid_definition
        return self.app.put_json('/models/%s' % self.model_id,
                                 {'definition': data},
                                 headers=self.headers)

    def create_data(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/models/%s/records' % self.model_id,
                                  data, headers=self.headers)

    def create_data_resp(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/models/%s/records' % self.model_id,
                                  data,
                                  headers=self.headers)

    def test_normal_definition_creation(self):
        self.create_definition()

    def test_malformed_definition_creation(self):
        resp = self.app.put_json('/models/%s' % self.model_id,
                                 {'definition': self.definition_without_title},
                                 headers=self.headers,
                                 status=400)
        self.assertIn('"name": "title"', resp.body.decode('utf-8'))

    def test_definition_creation_rejects_malformed_data(self):
        resp = self.app.put('/models/%s' % self.model_id,
                            {'definition': self.malformed_definition},
                            headers=self.headers,
                            status=400)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))

    def test_definition_retrieval(self):
        self.create_definition()

        # Verify that the schema is the same
        resp = self.app.get('/models/%s/definition' % self.model_id,
                            headers=self.headers)
        definition = force_unicode(self.valid_definition)
        self.assertDictEqual(resp.json, definition)

    def test_model_deletion(self):
        resp = self.create_definition()
        resp = self.create_data()
        record_id = resp.json['id']
        resp = self.app.delete('/models/%s' % self.model_id,
                               headers=self.headers)
        self.assertIn('name', resp.body.decode('utf-8'))
        self.assertRaises(RecordNotFound,
                          self.db.get_record, self.model_id, record_id)
        self.assertRaises(ModelNotFound, self.db.get_model_definition,
                          self.model_id)

    def test_normal_data_creation(self):
        self.create_definition()

        # Put data against this definition
        resp = self.app.post_json('/models/%s/records' % self.model_id,
                                  self.valid_data, headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))

    def test_invalid_data_validation(self):
        self.create_definition()

        # Try to put invalid data to this definition
        resp = self.app.post_json('/models/%s/records' % self.model_id,
                                  self.invalid_data,
                                  headers=self.headers,
                                  status=400)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))

    def test_data_retrieval(self):
        self.create_definition()
        resp = self.create_data()

        # Put valid data against this definition
        self.assertIn('id', resp.body.decode('utf-8'))

        record_id = resp.json['id']
        resp = self.app.get('/models/%s/records/%s' % (self.model_id,
                                                       record_id),
                            headers=self.headers)
        self.assertDataCorrect(resp.json, force_unicode(self.valid_data))

    def assertDataCorrect(self, data, entry):
        self.assertEqual(data, entry)

    def test_record_update(self):
        self.create_definition()
        # Put data against this definition
        entry = self.valid_data.copy()
        resp = self.create_data(entry)
        record_id = resp.json['id']

        # Update this data
        self.update_data(entry)
        resp = self.app.put_json('/models/%s/records/%s' % (self.model_id,
                                                            record_id),
                                 entry,
                                 headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))
        records = self.db.get_records(self.model_id)
        self.assertEqual(len(records), 1)

    def test_data_partial_update(self):
        self.create_definition()

        # Put data against this definition
        entry = self.valid_data.copy()
        resp = self.create_data(entry)
        record_id = resp.json['id']

        # Update this data
        self.update_data(entry)
        resp = self.app.patch_json('/models/%s/records/%s' % (self.model_id,
                                                              record_id),
                                   entry, headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))

        # Check that we only have one value in the db (e.g that PATCH didn't
        # created a new record)
        record = self.db.get_record(self.model_id, record_id)

        new_item = self.valid_data.copy()
        new_item.update(entry)
        self.assertEquals(record, new_item)

    def test_data_deletion(self):
        self.create_definition()
        resp = self.create_data()
        record_id = resp.json['id']
        # Test 200
        resp = self.app.delete(
            six.text_type('/models/%s/records/%s' % (self.model_id,
                                                     record_id)),
            headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))
        self.assertRaises(RecordNotFound, self.db.get_record,
                          self.model_id, record_id)
        # Test 404
        self.app.delete(
            six.text_type('/models/%s/records/%s' % (self.model_id,
                                                     record_id)),
            headers=self.headers, status=404)

    def test_unknown_data_returns_404(self):
        self.create_definition()
        self.app.get(
            six.text_type('/models/%s/records/%s' % (self.model_id, 1234)),
            headers=self.headers, status=404)

    def test_data_validation(self):
        self.create_definition()
        headers = self.headers.copy()
        headers['X-Daybed-Validate-Only'] = 'true'
        self.app.post_json('/models/%s/records' % self.model_id,
                           self.valid_data,
                           headers=headers, status=200)

        # no data should be added
        response = self.app.get('/models/%s/records' % self.model_id,
                                headers=self.headers)
        self.assertEquals(0, len(response.json['data']))
        # of course, pushing weird data should tell what's wrong
        response = self.app.post_json('/models/%s/records' % self.model_id,
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
            "title": u"simple — with unicode data in it",
            "description": "One optional field",
            "fields": [{"name": "age", "type": "int", "required": False,
                        "description": u"Put your âge"}]
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
                    "description": "The item",
                    "required": True,
                },
                {
                    "name": "status",
                    "type": "enum",
                    "choices": [
                        "done",
                        "todo"
                    ],
                    "required": True,
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
                    "description": "created on",
                    "required": True,
                    "auto_now": False
                },
                {
                    "name": "modified",
                    "type": "datetime",
                    "description": "modified on",
                    "required": True,
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

    def assertDataCorrect(self, data, entry):
        self.assertEqual(data['creation'], entry['creation'])
        # Check that auto-now worked
        self.assertNotEqual(data['modified'], entry['creation'])


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
                    "required": True,
                    "description": "Species"
                },
                {
                    "name": "location",
                    "type": "polygon",
                    "gps": True,
                    "required": True,
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

    def assertDataCorrect(self, data, entry):
        self.assertEqual(data['mushroom'], entry['mushroom'])
        # Check that polygon was closed automatically
        self.assertNotEqual(data['location'], entry['location'])
        self.assertEqual(data['location'][0][0], data['location'][0][-1])

    def test_data_geojson_retrieval(self):
        resp = self.create_definition()
        self.assertIn('id', resp.body.decode('utf-8'))
        resp = self.create_data()
        self.assertIn('id', resp.body.decode('utf-8'))

        headers = self.headers.copy()
        headers['Accept'] = 'application/json'
        resp = self.app.get('/models/%s/records' % self.model_id,
                            headers=headers)
        self.assertIn('data', resp.json)

        headers['Accept'] = 'application/geojson'
        resp = self.app.get('/models/%s/records' % (self.model_id),
                            headers=headers)
        self.assertIn('features', resp.json)

        features = resp.json['features']
        feature = features[0]
        self.assertIsNotNone(feature.get('id'))
        self.assertEquals(feature['properties']['mushroom'], 'Boletus')
        self.assertIsNone(feature['properties'].get('location'))
        self.assertEquals(feature['geometry']['type'], 'Polygon')
        # after update
        self.assertCountEqual(feature['geometry']['coordinates'],
                              [[[0, 0], [0, 1], [1, 1], [0, 0]]])


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
                    "required": True,
                    "description": "Administrative"
                },
                {
                    "name": "location",
                    "type": "point",
                    "gps": True,
                    "required": True,
                    "description": "(x,y,z)"
                }
            ]
        }

    @property
    def valid_data(self):
        return {'name': u'Nuestra Señora de La Paz',  # Add some unicode data
                'location': [-16.5, -68.15, 3500]}

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
                    "required": True,
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
