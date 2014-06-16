import colander

from daybed import schemas
from daybed.tests.support import unittest, BaseWebTest


OBJECT_FIELD_DEFINITION = {
    'name': u'tasks',
    'type': u'list',
    'hint': u'An object',
    'label': u'',
    'required': True,
    'itemtype': u'int'
}


class ListFieldTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.validator = schemas.ListField.validation(**self.definition)

    def test_can_be_defined_with_a_field_type(self):
        field = self.schema.deserialize(self.definition)
        self.assertDictEqual(self.definition, field)

    def test_is_not_valid_if_field_type_unknown(self):
        self.definition['itemtype'] = 'asteroid'
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
        self.definition.pop('itemtype')
        self.validator = schemas.ListField.validation(**self.definition)

    def test_validation_succeeds_if_items_are_valid(self):
        value = self.validator.deserialize('[1,"a",{"status": false}]')
        self.assertEquals(value, [1, u'a', {u'status': False}])


class ItemTypeListTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.definition['itemtype'] = 'date'
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
        self.definition = OBJECT_FIELD_DEFINITION.copy()
        self.definition['itemtype'] = 'object'
        self.definition['parameters'] = {
            'fields': [
                {'type': u'enum',
                 'name': u'status',
                 'choices': [u'todo', u'done']}
            ]
        }
        self.validator = schemas.ListField.validation(**self.definition)

    def test_is_not_valid_if_parameters_are_invalid(self):
        self.definition['parameters']['fields'] = []
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
