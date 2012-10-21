import os

import unittest
import webtest


HERE = os.path.dirname(os.path.abspath(__file__))


class FunctionaTest(unittest.TestCase):

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

    def setUp(self):
        # delete the db
        self.app = webtest.TestApp("config:tests.ini",  relative_to=HERE)

    def tearDown(self):
        pass

    def test_normal_definition_creation(self):
        resp = self.app.put_json('/definitions/todo',
                    self.valid_definition,
                    headers=self.headers)


    def test_malformed_definition_creation(self):
        pass

    def test_definition_creation_rejects_malformed_data(self):
        pass

    def test_definition_retrieval(self):
        pass

    def test_normal_validation(self):
        pass

    def test_normal_data_creation(self):
        pass

    def test_data_retrieval(self):
        pass

    def test_data_deletion(self):
        pass
