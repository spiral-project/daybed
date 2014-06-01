import colander

from daybed import schemas
from daybed.tests.support import unittest


class ListFieldTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = {
            'name': u'tasks',
            'type': u'list',
            'hint': u'An object',
            'label': u'',
            'required': True,
            'itemtype': u'int'
        }
        self.validator = schemas.ListField.validation(**self.definition)

    def test_can_be_defined_with_a_field_type(self):
        field = self.schema.deserialize(self.definition)
        self.assertDictEqual(self.definition, field)

    def test_is_not_valid_if_field_type_unknown(self):
        self.definition['itemtype'] = 'asteroid'
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_validation_succeeds_if_fields_are_valid(self):
        value = self.validator.deserialize('[1,3,4]')
        self.assertEquals(value, [1, 3, 4])
