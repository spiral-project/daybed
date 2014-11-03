import copy

import colander

from daybed import schemas
from daybed.tests.support import unittest, BaseWebTest


OBJECT_FIELD_DEFINITION = {
    'name': u'tasks',
    'type': u'list',
    'hint': u'An object',
    'item': {'type': u'int',
             'hint': u'An integer'}
}


class ListFieldTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = copy.deepcopy(OBJECT_FIELD_DEFINITION)
        self.validator = schemas.ListField.validation(**self.definition)

    def test_can_be_defined_with_a_field_type(self):
        field = self.schema.deserialize(self.definition)
        for defaultattr in ['required', 'label']:
            field.pop(defaultattr)
            field['item'].pop(defaultattr)
        self.assertDictEqual(self.definition, field)

    def test_is_not_valid_if_field_type_unknown(self):
        self.definition['item']['type'] = 'asteroid'
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_validation_succeeds_if_items_are_valid(self):
        value = self.validator.deserialize('[1,3,4]')
        self.assertEquals(value, [1, 3, 4])

    def test_validation_succeeds_if_no_items(self):
        value = self.validator.deserialize('[]')
        self.assertEquals(value, [])

    def test_validation_fails_if_items_malformed(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '[1,,3]')

    def test_validation_fails_if_items_are_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '[1, "a" ,4]')


class NoItemTypeListTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.definition.pop('item')
        self.validator = schemas.ListField.validation(**self.definition)

    def test_no_item_type_validation_is_performed(self):
        value = self.validator.deserialize('[1,"a",{"status": false}]')
        self.assertEquals(value, [1, u'a', {u'status': False}])


class ItemTypeListTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = copy.deepcopy(OBJECT_FIELD_DEFINITION)
        self.definition['item']['type'] = 'date'
        self.validator = schemas.ListField.validation(**self.definition)

    def test_validation_succeeds_if_items_are_valid(self):
        value = self.validator.deserialize('["2012-04-01", "2014-06-01"]')
        self.assertEquals(value, ["2012-04-01", "2014-06-01"])

    def test_validation_succeeds_if_items_are_comma_separated(self):
        value = self.validator.deserialize('2012-04-01, 2014-06-01')
        self.assertEquals(value, ["2012-04-01", "2014-06-01"])

    def test_validation_fails_if_items_are_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '["2012-33-01", "2014-06-01"]')


class ObjectListTest(BaseWebTest):

    def setUp(self):
        super(ObjectListTest, self).setUp()
        self.schema = schemas.ListField.definition()
        self.definition = copy.deepcopy(OBJECT_FIELD_DEFINITION)
        self.definition['item'] = {
            'type': 'object',
            'fields': [
                {'type': u'enum',
                 'name': u'status',
                 'choices': [u'todo', u'done']}
            ]
        }
        self.validator = schemas.ListField.validation(**self.definition)

    def test_is_not_valid_if_parameters_are_invalid(self):
        self.definition['item']['fields'] = []
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_validation_succeeds_if_items_are_valid(self):
        value = self.validator.deserialize('[{"status": "todo"},'
                                           ' {"status": "done"}]')
        self.assertEquals(value, [{'status': 'todo'}, {'status': 'done'}])

    def test_validation_fails_if_items_are_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '[{"status": "todo"}, {"status": "3.14"}]')

    def test_validation_sets_default_values(self):
        self.definition['item']['fields'].append({
            'type': 'date',
            'name': 'created',
            'autonow': True})
        self.validator = schemas.ListField.validation(**self.definition)
        values = self.validator.deserialize('[{"status": "todo"}]')
        self.assertIsNotNone(values[0].get('created'))
