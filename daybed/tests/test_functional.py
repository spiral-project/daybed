# -*- coding: utf-8 -*-
import json

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
        if not hasattr(self, 'assertCountEqual'):
            self.assertCountEqual = self.assertItemsEqual

    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.create_definition()

    @property
    def valid_definition(self):
        raise NotImplementedError

    @property
    def valid_record(self):
        raise NotImplementedError

    @property
    def invalid_record(self):
        raise NotImplementedError

    def assertDataCorrect(self, data, entry):
        self.assertEqual(data, entry)

    def create_definition(self, data=None):
        if not data:
            data = self.valid_definition
        return self.app.put_json('/models/%s' % self.model_id,
                                 {'definition': data},
                                 headers=self.headers)

    def create_record(self, data=None):
        if not data:
            data = self.valid_record
        return self.app.post_json('/models/%s/records' % self.model_id,
                                  data, headers=self.headers)

    def test_normal_record_creation(self):
        # Put data against this definition
        resp = self.app.post_json('/models/%s/records' % self.model_id,
                                  self.valid_record, headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))

    def test_invalid_record_validation(self):
        # Try to put invalid data to this definition
        resp = self.app.post_json('/models/%s/records' % self.model_id,
                                  self.invalid_record,
                                  headers=self.headers,
                                  status=400)
        self.assertIn('"status": "error"', resp.body.decode('utf-8'))

    def test_record_retrieval(self):
        # Put valid data against this definition
        resp = self.create_record()
        self.assertIn('id', resp.body.decode('utf-8'))

        record_id = resp.json['id']
        resp = self.app.get('/models/%s/records/%s' % (self.model_id,
                                                       record_id),
                            headers=self.headers)
        valid_record = force_unicode(self.valid_record)
        valid_record["id"] = record_id
        self.assertDataCorrect(resp.json, valid_record)

    def test_record_update(self):
        # Put data against this definition
        entry = self.valid_record.copy()
        resp = self.create_record(entry)
        record_id = resp.json['id']

        # Update this data
        self.update_record(entry)
        resp = self.app.put_json('/models/%s/records/%s' % (self.model_id,
                                                            record_id),
                                 entry,
                                 headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))
        records = self.db.get_records(self.model_id)
        self.assertEqual(len(records), 1)

    def test_record_partial_update(self):
        # Put data against this definition
        entry = self.valid_record.copy()
        resp = self.create_record(entry)
        record_id = resp.json['id']

        # Update this data
        self.update_record(entry)
        resp = self.app.patch_json('/models/%s/records/%s' % (self.model_id,
                                                              record_id),
                                   entry, headers=self.headers)
        self.assertIn('id', resp.body.decode('utf-8'))

        # Check that we only have one value in the db (e.g that PATCH didn't
        # created a new record)
        record = self.db.get_record(self.model_id, record_id)

        new_item = self.valid_record.copy()
        new_item.update(entry)
        new_item["id"] = record_id
        self.assertEquals(record, new_item)

    def test_record_validation(self):
        headers = self.headers.copy()
        headers['Validate-Only'] = 'true'
        self.app.post_json('/models/%s/records' % self.model_id,
                           self.valid_record,
                           headers=headers, status=200)

        # no data should be added
        response = self.app.get('/models/%s/records' % self.model_id,
                                headers=self.headers)
        self.assertEquals(0, len(response.json['records']))
        # of course, pushing weird data should tell what's wrong
        response = self.app.post_json('/models/%s/records' % self.model_id,
                                      self.invalid_record,
                                      headers=headers, status=400)
        # make sure the field name in cause is provided
        self.assertIn('errors', response.json)
        errors = response.json['errors']
        self.assertTrue(len(errors) > 0)
        self.assertIn('name', errors[0])
        self.assertNotEquals('', errors[0]['name'])

    def test_data_search_without_filter(self):
        self.create_definition()
        self.create_record()
        query = {'query': {'match_all': {}}}
        resp = self.app.request('/models/%s/search/' % self.model_id,
                                method='GET',
                                body=json.dumps(query).encode(),
                                headers=self.headers)
        results = resp.json.get('hits', {}).get('hits', [])
        self.assertTrue(len(results) > 0)


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
                    "label": "The item",
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
                    "label": "is it done or not",
                    "display": "dropdown"
                }
            ]
        }

    @property
    def valid_record(self):
        return {'item': 'My task', 'status': 'todo'}

    @property
    def invalid_record(self):
        return {'item': 'Invalid task', 'status': 'yay'}

    def update_record(self, entry):
        entry['status'] = 'done'

    def test_definition_creation_does_keep_metadata_fields(self):
        resp = self.app.get('/models/%s/definition' % self.model_id,
                            headers=self.headers)
        self.assertEquals(resp.json["fields"][1]["display"], "dropdown")


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
                    "label": "Species"
                },
                {
                    "name": "location",
                    "type": "polygon",
                    "gps": True,
                    "required": True,
                    "label": "Area spotted"
                }
            ]
        }

    @property
    def valid_record(self):
        return {'mushroom': 'Boletus',
                'location': [[[0, 0], [0, 1], [1, 1]]]}

    @property
    def invalid_record(self):
        return {'mushroom': 'Boletus',
                'location': [[0, 0], [0, 1]]}

    def update_record(self, entry):
        entry['location'] = [[[0, 0], [0, 2], [2, 2]],
                             [[0.5, 0.5], [0.5, 1], [1, 1]]]

    def assertDataCorrect(self, data, entry):
        self.assertEqual(data['mushroom'], entry['mushroom'])
        # Check that polygon was closed automatically
        self.assertNotEqual(data['location'], entry['location'])
        self.assertEqual(data['location'][0][0], data['location'][0][-1])

    def test_records_geojson_retrieval(self):
        resp = self.create_definition()
        self.assertIn('id', resp.body.decode('utf-8'))
        resp = self.create_record()
        self.assertIn('id', resp.body.decode('utf-8'))

        headers = self.headers.copy()
        headers['Accept'] = 'application/json'
        resp = self.app.get('/models/%s/records' % self.model_id,
                            headers=headers)
        self.assertIn('records', resp.json)

        headers['Accept'] = 'application/vnd.geo+json'
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


class AnnotationModelTest(BaseWebTest):

    def test_annotation_attribute_can_be_provided(self):
        resp = self.app.put_json('/models/annotation', {
            'definition': {
                "title": "annotation",
                "description": "A list of my stuff to do",
                "fields": [
                    {
                        "type": "annotation",
                        "label": "The annotation item",
                        "anotherField": "haha"
                    }
                ]
            }
        }, headers=self.headers)

        resp = self.app.get('/models/annotation', headers=self.headers)
        self.assertEquals(
            resp.json['definition']['fields'][0],
            {
                u'label': u'The annotation item',
                u'type': u'annotation',
                u'anotherField': u'haha'
            }
        )
