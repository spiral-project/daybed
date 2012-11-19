import pyramid.testing
import colander

from daybed import schemas
from daybed.tests.support import unittest


class TypeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.types = schemas.TypeRegistry()

    def tearDown(self):
        pyramid.testing.tearDown()

    def test_register(self):
        # Register a type
        self.types.register('foo', None)
        self.assertEqual(['foo'], self.types.names)

    def test_unregister_unknown(self):
        # Unregister unknown
        self.assertRaises(schemas.NotRegisteredError,
                          self.types.unregister, 'foo')

    def test_unregister(self):
        self.assertEqual([], self.types.names)

    def test_register_again(self):
        self.types.register('foo', None)
        self.assertRaises(schemas.AlreadyRegisteredError,
                          self.types.register, 'foo', None)

    def test_regex(self):
        schema = schemas.RegexField.definition()
        definition = schema.deserialize(
            {'description': 'Some field',
             'name': 'number',
             'type': 'regex',
             'regex': '\d+'})

        validator = schemas.RegexField.validation(**definition)
        self.assertEquals(1, int(validator.deserialize('1')))
        self.assertRaises(colander.Invalid, validator.deserialize, 'a')
