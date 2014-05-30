import colander

from daybed import schemas
from daybed.tests.support import BaseWebTest


class ObjectFieldTest(BaseWebTest):

    def setUp(self):
        super(ObjectFieldTest, self).setUp()
        self.schema = schemas.ObjectField.definition()
        self.definition = {
            'name': u'status',
            'type': u'object',
            'hint': u'An object',
            'label': u'',
            'required': True,
            'fields': [{'type': u'boolean',
                        'name': u'done'},
                       {'type': u'datetime',
                        'name': u'updated'}]}
        self.validator = schemas.ListField.validation(**self.definition)

    def _create_definition(self, **kwargs):
        fakedef = {'title': 'stupid', 'description': 'stupid',
                   'fields': [{"name": "age", "type": "int",
                               "required": False}]}
        fakedef.update(**kwargs)
        return self.app.put_json('/models/simple',
                                 {'definition': fakedef},
                                 headers=self.headers)

    def test_is_defined_without_model_and_fields(self):
        self.definition.pop('fields')
        self.schema.deserialize(self.definition)

    def test_is_not_valid_if_both_fields_and_model(self):
        self.definition['model'] = 'Foo'
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_defined_with_an_existing_model(self):
        self.definition.pop('fields')
        self._create_definition()
        self.definition['model'] = 'simple'
        self.schema.deserialize(self.definition)

    def test_is_not_valid_if_model_unknown(self):
        self.definition.pop('fields')
        self.definition['model'] = 'simple'
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_defined_with_valid_fields(self):
        field = self.schema.deserialize(self.definition)
        default_attrs = {
            'label': u'',
            'hint': u'',
            'required': True,
        }
        self.definition['fields'][0].update(default_attrs)
        self.definition['fields'][1].update(default_attrs)
        self.assertDictEqual(self.definition, field)

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
