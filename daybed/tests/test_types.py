
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
        self.assertEqual([], self.types.names)
        self.types.register('foo', None)
        self.assertEqual(['foo'], self.types.names)
        # Unregister unknown
        self.assertRaises(schemas.NotRegisteredError,
                          self.types.unregister, 'bar')
        # Unregister the type
        self.types.unregister('foo')
        self.assertEqual([], self.types.names)
        # Unregister again
        self.assertRaises(schemas.NotRegisteredError,
                          self.types.unregister, 'foo')

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
