import pyramid.testing
import colander

from daybed import schemas
from daybed.schemas import (TypeRegistry, NotRegisteredError,
                            AlreadyRegisteredError, UnknownFieldTypeError)
from daybed.tests.support import unittest


class TypeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.types = TypeRegistry()

    def tearDown(self):
        pyramid.testing.tearDown()

    def test_register(self):
        # Register a type
        self.assertEqual([], list(self.types.names))
        self.types.register('foo', None)
        self.assertEqual(['foo'], list(self.types.names))

    def test_unregister_unknown(self):
        # Unregister unknown
        self.assertRaises(NotRegisteredError,
                          self.types.unregister, 'foo')

    def test_unregister(self):
        self.types.register('bar', None)
        self.assertEqual(['bar'], list(self.types.names))
        self.types.unregister('bar')
        self.assertEqual([], list(self.types.names))
        self.assertRaises(UnknownFieldTypeError,
                          self.types.definition, 'bar')
        self.assertRaises(UnknownFieldTypeError,
                          self.types.validation, 'bar')

    def test_register_again(self):
        self.types.register('foo', None)
        self.assertRaises(AlreadyRegisteredError,
                          self.types.register, 'foo', None)


class RolesValidatorTests(unittest.TestCase):
    def test_roles(self):
        schema = schemas.RolesValidator()
        self.assertRaises(colander.Invalid, schema.deserialize, {})
        self.assertRaises(colander.Invalid, schema.deserialize,
                          {'admins': 'not-a-sequence'})
        self.assertEquals(schema.deserialize(
            {'admins': ['Remy', 'Alexis']}),
            {'admins': ['Remy', 'Alexis']})

        return
        # XXX: FIXME
        self.assertRaises(colander.Invalid, schema.deserialize,
                          {'admins': ['Test'],
                           'group:toto': 'not-a-sequence'})
