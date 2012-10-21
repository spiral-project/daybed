import json

from daybed.tests.support import BaseWebTest


class FunctionaTest(BaseWebTest):

    def __init__(self, *args, **kwargs):
        super(FunctionaTest, self).__init__(*args, **kwargs)
        self.valid_definition = {
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
            ]}

        self.definition_without_title = self.valid_definition.copy()
        self.definition_without_title.pop('title')
        self.valid_data = {'item': 'My task', 'status': 'todo'}
        self.malformed_definition = '{"test":"toto", "titi": "tutu'
        self.invalid_data = {'item': 'Invalid task', 'status': 'yay'}
        self.headers = {'Content-Type': 'application/json'}

    def create_definition(self, data=None):
        if not data:
            data = self.valid_definition

        return self.app.put_json('/definitions/todo', data,
                                 headers=self.headers)

    def create_data(self, data=None):
        if not data:
            data = self.valid_data
        return self.app.post_json('/data/todo', data,
                                  headers=self.headers)

    def test_normal_definition_creation(self):
        resp = self.create_definition()
        self.assertIn('token', resp.body)

    def test_malformed_definition_creation(self):
        resp = self.app.put_json('/definitions/todo',
                    self.definition_without_title,
                    headers=self.headers,
                    status=400)
        self.assertIn('"name": "title"', resp.body)

    def test_definition_creation_rejects_malformed_data(self):
        resp = self.app.put('/definitions/todo',
                    self.malformed_definition,
                    headers=self.headers,
                    status=400)
        self.assertIn('"status": "error"', resp.body)

    def test_definition_retrieval(self):
        self.create_definition()

        # Verify that the schema is the same
        resp = self.app.get('/definitions/todo', headers=self.headers)
        self.assertEqual(json.loads(resp.body), self.valid_definition)

    def test_normal_validation(self):
        # Not Implemented yet
        pass

    def test_normal_data_creation(self):
        self.create_definition()

        # Put data against this definition
        resp = self.app.post_json('/data/todo',
                                 {'item': 'My task',
                                  'status': 'todo'},
                                 headers=self.headers)
        self.assertIn('id', resp.body)

    def test_invalid_data_validation(self):
        self.create_definition()

        # Try to put invalid data to this definition
        resp = self.app.post_json('/data/todo',
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

        data_item_id = json.loads(resp.body)['id']
        resp = self.app.get('/data/todo/%s' % data_item_id,
                            headers=self.headers)
        entry = self.valid_data.copy()
        entry['id'] = data_item_id
        self.assertEqual(json.loads(resp.body), entry)

    def test_data_update(self):
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)

        # Put data against this definition
        entry = {'item': 'My task', 'status': 'todo'}
        resp = self.app.post_json('/data/todo',
                                 entry,
                                 headers=self.headers)
        data_item_id = json.loads(resp.body)['id']

        # Update this data
        entry['status'] = 'done'
        resp = self.app.put_json(str('/data/todo/%s' % data_item_id),
                                 entry,
                                 headers=self.headers)
        self.assertIn('id', resp.body)

    def test_data_deletion(self):
        pass

    def test_data_validation(self):
        self.create_definition()
        headers = self.headers.copy()
        headers['X-Daybed-Validate-Only'] = 'true'
        self.app.post_json('/data/todo', self.valid_data,
                           headers=headers, status=200)

        # no data should be added
        self.assertEquals(0, len(self.app.get('/data/todo').json['data']))
        # of course, pushing weird data should tell what's wrong
        self.app.post_json('/data/todo', self.invalid_data,
                           headers=headers, status=400)
