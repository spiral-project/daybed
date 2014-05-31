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
         'hint': u'',
         'required': True},
        {'type': u'datetime',
         'name': u'updated',
         'label': u'',
         'hint': u'',
         'required': True,}
    ]
}


class InvalidObjectFieldTest(BaseWebTest):

    def setUp(self):
        super(InvalidObjectFieldTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()

    def test_is_not_valid_if_both_fields_and_model(self):
        self.definition['model'] = 'Foo'
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


class FieldsObjectTest(BaseWebTest):
    def setUp(self):
        super(FieldsObjectTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        # self.validator = schemas.ListField.validation(**self.definition)

    def test_is_defined_with_valid_fields(self):
        field = self.schema.deserialize(self.definition)
        self.assertDictEqual(self.definition, field)


class FreeObjectTest(BaseWebTest):
    def setUp(self):
        super(FreeObjectTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.definition.pop('fields')

    def test_is_defined_without_model_and_fields(self):
        field = self.schema.deserialize(self.definition)
        self.assertDictEqual(self.definition, field)


class ModelFieldTest(BaseWebTest):
    def setUp(self):
        super(ModelFieldTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.definition.pop('fields')
        self._create_definition()
        self.definition['model'] = 'simple'

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
