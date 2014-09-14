import mock
import colander
from cornice.errors import Errors
from pyramid.testing import DummyRequest

from daybed import schemas
from daybed.schemas.validators import validator
from daybed.tests.support import unittest


class ValidatorTests(unittest.TestCase):
    def test_adds_body_error_if_json_invalid(self):
        request = DummyRequest()
        request.body = b'{wrong,"format"}'
        request.errors = Errors()
        validator(request, mock.Mock())
        self.assertEqual('body', request.errors[0]['location'])



class DefinitionSchemaTest(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.TypeField.definition()

    def test_field_type_is_required(self):
        self.assertRaises(colander.Invalid, self.schema.deserialize,
                          {'name': 'secret'})

    def test_field_type_must_be_known_from_registry(self):
        self.assertRaises(colander.Invalid, self.schema.deserialize,
                          {'name': 'a', 'type': 'b'})

    def test_field_name_can_contain_some_characters(self):
        good_names = ['a', 'B', 'a0', 'a_', 'a-b', 'Aa']
        for good_name in good_names:
            definition = self.schema.deserialize({'name': good_name,
                                                  'type': 'string'})
            self.assertEquals(definition['name'], good_name)

    def test_field_name_cannot_contain_bad_characters(self):
        bad_names = ['', '_', '-a', '0a', '_a', 'a b', 'a&a']
        for bad_name in bad_names:
            self.assertRaises(colander.Invalid, self.schema.deserialize,
                              {'name': bad_name, 'type': 'string'})

    def test_field_hint_takes_default_from_type_class(self):
        schema = schemas.StringField.definition()
        definition = schema.deserialize(
            {'name': 'no_hint',
             'type': 'string'})
        self.assertEquals(definition['hint'], schemas.StringField.hint)

    def test_field_hint_can_be_overriden(self):
        definition = self.schema.deserialize(
            {'name': 'secret',
             'type': 'string',
             'hint': 'A secret word'})
        self.assertEquals(definition['hint'], 'A secret word')

    def test_label_can_be_provided(self):
        definition = self.schema.deserialize(
            {'label': 'Some field',
             'name': 'address',
             'type': 'string'})
        self.assertEquals(definition.get('label'), 'Some field')

    def test_label_is_optional_and_empty_by_default(self):
        definition = self.schema.deserialize(
            {'name': 'firstname',
             'type': 'string'})
        self.assertEquals(definition['label'], '')

    def test_field_is_required_by_default(self):
        definition = self.schema.deserialize(
            {'name': 'firstname',
             'type': 'string'})
        self.assertEquals(definition['required'], True)

    def test_null_is_deserialized_if_field_is_not_required(self):
        definition = self.schema.deserialize(
            {'name': 'address',
             'type': 'int',
             'required': False})
        validator = schemas.TypeField.validation(**definition)
        self.assertEquals(colander.null, validator.deserialize(''))

    def test_deserialized_if_field_is_not_required_can_be_overridden(self):
        definition = self.schema.deserialize(
            {'name': 'address',
             'type': 'int',
             'required': False})
        before = schemas.TypeField.default_value
        schemas.TypeField.default_value = 0
        validator = schemas.TypeField.validation(**definition)
        self.assertEquals(0, validator.deserialize(''))
        schemas.TypeField.default_value = before


