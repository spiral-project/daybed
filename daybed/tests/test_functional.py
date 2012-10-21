import os
import json

import unittest
import webtest

from daybed.tests import BaseWebTest


HERE = os.path.dirname(os.path.abspath(__file__))


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
        self.headers = {'Content-Type': 'application/json'}

    def test_normal_definition_creation(self):
        resp = self.app.put_json('/definitions/todo',
                    self.valid_definition,
                    headers=self.headers)
        self.assertIn('token', resp.body)        

    def test_malformed_definition_creation(self):
        resp = self.app.put_json('/definitions/todo',
                    self.definition_without_title,
                    headers=self.headers,
                    status=400)
        self.assertIn('"name": "title"', resp.body)

    def test_definition_creation_rejects_malformed_data(self):
        resp = self.app.put('/definitions/todo',
                    '{"test":"toto", "titi": "tutu',
                    headers=self.headers,
                    status=400)
        self.assertIn('"status": "error"', resp.body)

    def test_definition_retrieval(self):
        # Put a valid JSON
        resp = self.app.put_json('/definitions/todo',
                    self.valid_definition,
                    headers=self.headers)

        # Verify that the schema is the same
        resp = self.app.get('/definitions/todo',
                    headers=self.headers)
        self.assertEqual(json.loads(resp.body), self.valid_definition)
        

    def test_normal_validation(self):
        # Not Implemented yet
        pass

    def test_normal_data_creation(self):
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)
        
        # Put data against this definition
        resp = self.app.post_json('/data/todo',
                                 {'item': 'My task',
                                  'status': 'todo'},
                                 headers=self.headers)
        self.assertIn('id', resp.body)

    def test_invalid_data_validation(self):
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)
        
        # Try to put invalid data to this definition
        resp = self.app.post_json('/data/todo',
                                 {'item': 'My task',
                                  'status': 'false'},
                                 headers=self.headers,
                                 status=400)
        self.assertIn('"status": "error"', resp.body)
        

    def test_data_retrieval(self):
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)
        
        # Put data against this definition
        entry = {'item': 'My task', 'status': 'todo'}
        resp = self.app.post_json('/data/todo',
                                 entry,
                                 headers=self.headers)
        self.assertIn('id', resp.body)

        data_item_id = json.loads(resp.body)['id']
        resp = self.app.get('/data/todo/%s' % data_item_id,
                            headers=self.headers)
        entry['id'] = data_item_id
        self.assertEqual(json.loads(resp.body), entry)

    def test_data_update(self):
        pass

    def test_data_deletion(self):
        pass
