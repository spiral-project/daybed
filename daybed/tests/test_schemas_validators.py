import mock
import colander
from cornice.errors import Errors
from pyramid.testing import DummyRequest

from daybed import schemas
from daybed.schemas import validators
from daybed.tests.support import unittest, BaseWebTest


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.request.db = mock.MagicMock()
        self.request.matchdict = mock.MagicMock()
        self.request.errors = Errors()
        self.request.body = b''

    def test_adds_body_error_if_json_invalid(self):
        self.request.body = b'{wrong,"format"}'
        validators.validator(self.request, mock.Mock())
        self.assertEqual('body', self.request.errors[0]['location'])

    def test_records_validation_adds_errors_to_response(self):
        self.request.db.get_model_definition.return_value = {
            'fields': [{
                'name': 'wishlist',
                'type': 'list',
                'item': {
                    'type': 'object',
                    'fields': [{'name': 'wish', 'type': 'string'}]
                }
            }]
        }
        self.request.body = b'{"wishlist": [{"wish": "A"}, {"wish": 3.14}]}'
        validators.record_validator(self.request)
        self.assertEqual(len(self.request.errors), 1)
        self.assertIn('1.wish', self.request.errors[0]['name'])
        self.assertIn('3.14', self.request.errors[0]['description'])

    def test_posted_data_is_postprocessed_recursively(self):
        data = {"records": [{"name": colander.null}]}
        schema_mock = mock.Mock()
        schema_mock.deserialize.return_value = data
        validators.validator(self.request, schema_mock)
        self.assertIsNone(self.request.data_clean['records'][0].get('name'))


class RecordValidatorTest(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.TypeField.definition()

    def test_raises_invalid_if_falsy_value_is_provided(self):
        definition = {
            'name': 'name',
            'type': 'object',
            'fields': [{'name': 'first', 'type': 'string'}]}
        validator = schemas.ObjectField.validation(**definition)
        self.assertRaises(colander.Invalid, validator.deserialize,
            {'first': None})
        self.assertRaises(colander.Invalid, validator.deserialize,
            {"first": ""})
        self.assertRaises(colander.Invalid, validator.deserialize,
            '{"first": null}')

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

    def test_extra_may_be_present(self):
        schema = validators.DefinitionSchema()
        definition = schema.deserialize({
            "title": "Foobar",
            "description": "foo bar",
            "extra": {
                "submitButtonLabel": "Let's go!",
            },
            "fields": [
                {'type': 'annotation',
                 'label': 'this is some content'}
            ]
        })
        self.assertIn("extra", definition)
        self.assertIn("submitButtonLabel", definition["extra"])
        self.assertEqual("Let's go!", definition["extra"]["submitButtonLabel"])

    def test_extra_may_not_be_present(self):
        schema = validators.DefinitionSchema()
        definition = schema.deserialize({
            "title": "Foobar",
            "description": "foo bar",
            "fields": [
                {'type': 'annotation',
                 'label': 'this is some content'}
            ]
        })
        self.assertNotIn("extra", definition)


class ModelSchemaTest(unittest.TestCase):

    def setUp(self):
        self.schema = validators.ModelSchema()
        self.definition = {
            'title': u'Flavors',
            'description': u'Flavors',
            'fields': [{'type': 'string', 'name': 'flavor'}]
        }

    def test_fails_if_no_definition(self):
        incomplete = {'records': []}
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize, incomplete)

    def test_fails_if_definition_is_invalid(self):
        definition = self.definition.copy()
        definition.pop('title')
        invalid = {'definition': definition}
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize, invalid)

    def test_succeeds_if_only_definition(self):
        minimal = {'definition': self.definition}
        validated = self.schema.deserialize(minimal)
        self.assertEqual(self.definition['title'],
                         validated['definition']['title'])

    def test_succeeds_if_record_matches_definition(self):
        with_records = {'definition': self.definition,
                        'records': [{'flavor': 'vanilla'}]}
        validated = self.schema.deserialize(with_records)
        self.assertEqual(self.definition['title'],
                         validated['definition']['title'])

    def test_fails_if_record_is_invalid_for_definition(self):
        with_records = {'definition': self.definition,
                        'records': [{'flavor': 3.14}]}
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize, with_records)

    def test_record_raises_one_error_by_field(self):
        with_records = {'definition': self.definition,
                        'records': [{'flavor': 3.14}]}
        try:
            self.schema.deserialize(with_records)
        except colander.Invalid as e:
            self.assertEqual(len(e.children), 1)


class PermissionsSchemaTest(BaseWebTest):

    def setUp(self):
        super(PermissionsSchemaTest, self).setUp()
        self.db.store_credentials('abc', {'id': 'doctor', 'key': 'who'})
        self.schema = validators.PermissionsSchema(name='permissions')
        self.permissions = {
            'doctor': ['ALL'],
            'Everyone': ['read_own_records'],
        }

    def test_fails_if_not_a_mapping(self):
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize, ['doctor'])

    def test_fails_if_identifier_is_unknown(self):
        unknown = self.permissions.copy()
        unknown['unknown'] = ['delete_model']
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize, unknown)

    def test_unknown_identifier_is_given_in_error(self):
        unknown = self.permissions.copy()
        unknown['unknown'] = ['delete_model']
        try:
            self.schema.deserialize(unknown)
        except colander.Invalid as e:
            self.assertIn(u"Credentials id 'unknown' could not be found.",
                          repr(e))

    def test_shortcut_identifiers_are_replaced_by_system_principals(self):
        shortcuts = self.permissions.copy()
        shortcuts['Authenticated'] = ['delete_model']
        value = self.schema.deserialize(shortcuts)
        self.assertIsNone(value.get('Everyone'))
        self.assertEqual(value['system.Everyone'], ['read_own_records'])
        self.assertIsNone(value.get('Authenticated'))
        self.assertEqual(value['system.Authenticated'], ['delete_model'])

    def test_fails_if_permission_name_is_unknown(self):
        unknown = self.permissions.copy()
        unknown['Everyone'] = ['drink_coffee']
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize, unknown)

    def test_unknown_permissions_are_given_in_errors(self):
        unknown = self.permissions.copy()
        unknown['Everyone'].append('drink_coffee')
        try:
            self.schema.deserialize(unknown)
        except colander.Invalid as e:
            self.assertIn('"drink_coffee" is not one of ', str(e))

    def test_all_becomes_lowercase(self):
        value = self.schema.deserialize(self.permissions)
        self.assertEqual(value['doctor'], ['ALL'])

    def test_permissions_can_be_specified_with_plus(self):
        with_plus = self.permissions.copy()
        with_plus['doctor'] = ['+read_own_records']
        value = self.schema.deserialize(with_plus)
        self.assertEqual(value['doctor'], ['+read_own_records'])

    def test_permissions_can_be_specified_with_minus(self):
        with_minus = self.permissions.copy()
        with_minus['doctor'].append('-read_all_records')
        value = self.schema.deserialize(with_minus)
        self.assertEqual(value['doctor'], ['ALL', '-read_all_records'])
