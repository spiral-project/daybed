import unittest
import json

from pyramid import testing
from webtest import TestApp


class TestModelDefinition(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.app = TestApp("config:development.ini",  relative_to="./")

    def tearDown(self):
        testing.tearDown()

    def put_json(self, path, params, status):
        response = self.app.put(path,
                                params=json.dumps(params),
                                status=status).json
        return response

    def test_definition_misuse(self):
        path = '/definition'
        # Empty model name
        self.app.put(path, status=404)
        self.app.post(path, status=404)
        self.app.get(path, status=404)
        # With model name
        path = '/definition/mushroom'
        # Wrong method
        self.app.post(path, status=405)
        # No data
        self.app.put(path, status=400)
        # Malformed json
        self.put_json(path, "{'X'-: 4}", 400)
        # Wrong definitions
        model = {'title': 'Mushroom'}
        response = self.put_json(path, model, 400)
        self.assertEqual(response['status'], 'error')
        # No fields
        model = {
            'title': 'Mushroom',
            'description': 'Mushroom picking areas',
        }
        response = self.put_json(path, model, 400)
        self.assertEqual(response['errors'][0]['name'], 'fields')
        # With empty fields
        model['fields'] = []
        response = self.put_json(path, model, 400)
        self.assertEqual(response['errors'][0]['name'], 'fields')
        # With invalid fields
        model['fields'] = [{
            'name': 'untyped',
        }]
        response = self.put_json(path, model, 400)
        self.assertEqual(response['errors'][0]['name'], 'fields')

    def test_definition_creation(self):
        path = '/definition/mushroom'
        model = {
            'title': 'Mushroom',
            'description': 'Mushroom picking spot',
            'fields': [{
                'name': "place",
                'type': "string",
                'description': "Where ?",
            }]
        }
        response = self.put_json(path, model, 200)
        self.assertTrue('token' in response)
        # Get it back
        response = self.app.get(path, status=200).json
        self.assertEqual(response, model)
