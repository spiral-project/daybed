import colander

from daybed import schemas
from daybed.tests.support import unittest


class JSONFieldTests(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.JSONField.definition()
        definition = self.schema.deserialize({'name': 'test',
                                              'type': 'json'})
        self.validator = schemas.JSONField.validation(**definition)

    def test_deserialization_works_with_empty_object(self):
        self.assertEquals(self.validator.deserialize('{}'), {})

    def test_deserialization_fails_if_json_is_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '{yo:1}')

    def test_json_field_can_be_a_single_list(self):
        self.assertEquals(self.validator.deserialize('[1,"b",3]'),
                          [1, 'b', 3])

    def test_json_field_cannot_be_a_single_string(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, 'cf spec')

    def test_json_field_is_idempotent(self):
        self.assertEquals(self.validator.deserialize([1, 'b', 3]),
                          [1, 'b', 3])
