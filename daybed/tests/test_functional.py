from daybed.tests.support import BaseWebTest
from daybed.schemas import registry


class FunctionalTest(object):
    """These are the functional tests for daybed.

    The goal is to have them reproduce every possible scenario that we want to
    support in the application.

    The test suite is created in a way that each test is a different scenario.
    We reset the database each time we start a new test to avoid sharing
    context between tests.
    """

    model_name = None

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

    def create_definition(self, data=None):
        if not data:
            data = self.valid_definition
        return self.app.put_json('/definitions/%s' % self.model_name,
                                 data,
                                 headers=self.headers)

    def create_data(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/data/%s' % self.model_name,
                                  data,
                                  headers=self.headers)

    def create_data_resp(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/data/%s' % self.model_name,
                                  data,
                                  headers=self.headers)

    def test_normal_definition_creation(self):
        resp = self.create_definition()
        self.assertIn('token', resp.body)

    def test_malformed_definition_creation(self):
        resp = self.app.put_json('/definitions/%s' % self.model_name,
                    self.definition_without_title,
                    headers=self.headers,
                    status=400)
        self.assertIn('"name": "title"', resp.body)

    def test_definition_creation_rejects_malformed_data(self):
        resp = self.app.put('/definitions/%s' % self.model_name,
                    self.malformed_definition,
                    headers=self.headers,
                    status=400)
        self.assertIn('"status": "error"', resp.body)

    def test_definition_retrieval(self):
        self.create_definition()

        # Verify that the schema is the same
        resp = self.app.get('/definitions/%s' % self.model_name,
                            headers=self.headers)
        self.assertEqual(resp.json, self.valid_definition)

    def test_definition_deletion(self):
        resp = self.create_definition()
        token = resp.json['token']
        resp = self.create_data()
        data_item_id = resp.json['id']
        self.app.delete(str('/definitions/%s?token=%s' % (
                            self.model_name, token)))
        queryset = self.db.get_data_item(self.model_name,
                                         data_item_id)
        self.assertIsNone(queryset)
        queryset = self.db.get_definition(self.model_name)
        self.assertIsNone(queryset)

    def test_normal_data_creation(self):
        self.create_definition()

        # Put data against this definition
        resp = self.app.post_json('/data/%s' % self.model_name,
                                 self.valid_data,
                                 headers=self.headers)
        self.assertIn('id', resp.body)

    def test_invalid_data_validation(self):
        self.create_definition()

        # Try to put invalid data to this definition
        resp = self.app.post_json('/data/%s' % self.model_name,
                                  {'item': 'My task',
                                   'status': 'false'},
                                  headers=self.headers,
                                  status=400)
        self.assertIn('"status": "error"', resp.body)

    def test_data_retrieval(self):
        self.create_definition()
        resp = self.create_data()

        # Put valid data against this definition
        self.assertIn('id', resp.body)

        data_item_id = resp.json['id']
        resp = self.app.get('/data/%s/%s' % (self.model_name,
                                             data_item_id),
                            headers=self.headers)
        entry = self.valid_data.copy()
        # entry['id'] = str(data_item_id
        self.assertEqual(resp.json, entry)

    def test_data_update(self):
        self.create_definition()
        # Put data against this definition
        entry = self.valid_data.copy()
        resp = self.create_data(entry)
        data_item_id = resp.json['id']

        # Update this data
        self.update_data(entry)
        resp = self.app.put_json(str('/data/%s/%s' % (
                                     self.model_name,
                                     data_item_id)),
                                 entry,
                                 headers=self.headers)
        self.assertIn('id', resp.body)
        # Todo : Verify DB
        queryset = self.db.get_data(self.model_name)
        self.assertEqual(len(queryset), 1)

    def test_data_deletion(self):
        self.create_definition()
        resp = self.create_data()
        data_item_id = resp.json['id']
        self.app.delete(str('/data/%s/%s' % (self.model_name,
                                             data_item_id)))
        queryset = self.db.get_data_item(self.model_name,
                                         data_item_id)
        self.assertIsNone(queryset)

    def test_data_validation(self):
        self.create_definition()
        headers = self.headers.copy()
        headers['X-Daybed-Validate-Only'] = 'true'
        self.app.post_json('/data/%s' % self.model_name,
                           self.valid_data,
                           headers=headers, status=200)

        # no data should be added
        response = self.app.get('/data/%s' % self.model_name)
        self.assertEquals(0, len(response.json['data']))
        # of course, pushing weird data should tell what's wrong
        self.app.post_json('/data/%s' % self.model_name,
                           self.invalid_data,
                           headers=headers, status=400)

    def test_fields_are_listed(self):
        response = self.app.get('/fields')
        self.assertEquals(response.json, registry.names)


class TodoModelTest(FunctionalTest, BaseWebTest):

    model_name = 'todo'

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


class MushroomsModelTest(FunctionalTest, BaseWebTest):

    model_name = 'mushroom_spots'

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
                'location': '[[[0, 0], [0, 1], [1, 1]]]'}

    @property
    def invalid_data(self):
        return {'mushroom': 'Boletus',
                'location': '[[0, 0], [0, 1]]'}

    def update_data(self, entry):
        entry['location'] = '[[[0, 0], [0, 2], [2, 2]], [[0.5, 0.5], [0.5, 1], [1, 1]]]'
