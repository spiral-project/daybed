import copy
import datetime

import mock
import colander

from daybed import schemas
from daybed.tests.support import BaseWebTest


OBJECT_FIELD_DEFINITION = {
    'name': u'status',
    'type': u'object',
    'hint': u'An object',
    'label': u'',
    'required': True,
    'fields': [
        {'type': u'boolean',
         'name': u'done',
         'label': u'',
         'hint': u'True or false',
         'required': True},
        {'autonow': False,
         'type': u'datetime',
         'name': u'updated',
         'label': u'',
         'hint': u'A date with time (yyyy-mm-ddTHH:MM)',
         'required': True}
    ]
}


class InvalidObjectFieldTest(BaseWebTest):

    def setUp(self):
        super(InvalidObjectFieldTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = copy.deepcopy(OBJECT_FIELD_DEFINITION)

    def test_is_not_valid_if_both_fields_and_model(self):
        self.definition['model'] = 'Foo'
        with mock.patch('daybed.schemas.relations.ModelExist.__call__'):
            self.assertRaises(colander.Invalid,
                              self.schema.deserialize,
                              self.definition)

    def test_is_not_valid_if_no_fields_nor_model(self):
        self.definition.pop('fields')
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_not_valid_if_model_unknown(self):
        self.definition.pop('fields')
        self.definition['model'] = 'simple'
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_not_valid_if_field_structure_invalid(self):
        self.definition['fields'][0].pop('type')
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_not_valid_if_fields_list_is_empty(self):
        self.definition['fields'] = []
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_not_valid_if_field_type_unknown(self):
        self.definition['fields'][0]['type'] = 'asteroid'
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_not_valid_if_subfield_definition_is_invalid(self):
        self.definition['fields'][0]['type'] = 'enum'
        self.definition['fields'][0]['choices'] = []
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)


class FieldsObjectTest(BaseWebTest):
    def setUp(self):
        super(FieldsObjectTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.validator = schemas.ObjectField.validation(**self.definition)

    def test_is_defined_with_valid_fields(self):
        field = self.schema.deserialize(self.definition)
        self.assertDictEqual(self.definition, field)

    def test_validation_succeeds_if_fields_are_valid(self):
        value = self.validator.deserialize({"done": False,
                                            "updated": "2012-03-13"})
        updated = datetime.datetime(2012, 3, 13, 0, 0, 0, 0,
                                    colander.iso8601.UTC)
        self.assertDictEqual(value, {'done': False, 'updated': updated})

    def test_validation_succeeds_if_value_is_provided_as_json(self):
        value = self.validator.deserialize('{"done": false, '
                                           ' "updated": "2012-03-13"}')
        updated = datetime.datetime(2012, 3, 13, 0, 0, 0, 0,
                                    colander.iso8601.UTC)
        self.assertDictEqual(value, {'done': False, 'updated': updated})

    def test_validation_fails_if_field_value_is_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          {"done": False, "updated": "2012-23-13"})

    def test_validation_returns_deserialized_data(self):
        self.definition['fields'] = [{
            'type': u'date',
            'name': u'updated',
            'autonow': True}]
        validator = schemas.ObjectField.validation(**self.definition)
        value = validator.deserialize({})
        self.assertIsNotNone(value.get('updated'))


class ModelFieldTest(BaseWebTest):
    def setUp(self):
        super(ModelFieldTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.definition.pop('fields')
        self._create_definition()
        self.definition['model'] = 'simple'
        self.validator = schemas.ObjectField.validation(**self.definition)

    def _create_definition(self, **kwargs):
        fakedef = {'title': 'stupid', 'description': 'stupid',
                   'fields': [{"name": "age", "type": "int",
                               "required": False}]}
        fakedef.update(**kwargs)
        return self.app.put_json('/models/simple',
                                 {'definition': fakedef},
                                 headers=self.headers)

    def test_is_defined_with_an_existing_model(self):
        field = self.schema.deserialize(self.definition)
        self.assertDictEqual(self.definition, field)

    def test_validation_succeeds_if_fields_are_valid(self):
        value = self.validator.deserialize({"age": "12"})
        self.assertDictEqual(value, {'age': 12})

    def test_validation_succeeds_if_value_is_provided_as_json(self):
        value = self.validator.deserialize('{"age": "12"}')
        self.assertDictEqual(value, {'age': 12})

    def test_validation_fails_if_fields_is_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '{"age": "a"}')

    def test_validator_instantiation_fails_if_model_was_deleted(self):
        self.app.delete('/models/simple',
                        headers=self.headers)
        self.assertRaises(colander.Invalid,
                          schemas.ObjectField.validation,
                          **self.definition)
