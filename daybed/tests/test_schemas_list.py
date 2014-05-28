import colander

from daybed import schemas
from daybed.tests.support import unittest


class ListFieldTest(unittest.TestCase):

    def setUp(self):
        self.schema = schemas.ListField.definition()
        self.definition = {
            'name': u'tasks',
            'type': u'list',
            'subtype': [{'type': u'boolean',
                         'name': u'status',
                         'hint': u'',
                         'label': u'',
                         'required': True}]}
        self.validator = schemas.ListField.validation(**self.definition)

    def test_is_defined_with_a_valid_subschema(self):
        field = self.schema.deserialize(self.definition)
        self.definition.update({
            'label': u'',
            'hint': u'A list of objects',
            'required': True,
        })
        self.assertDictEqual(self.definition, field)

    def test_is_not_valid_if_subschema_invalid(self):
        self.definition['subtype'][0].pop('type')
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)

    def test_is_not_valid_if_subschema_is_empty(self):
        self.definition['subtype'] = []
        self.assertRaises(colander.Invalid,
                          self.schema.deserialize,
                          self.definition)
