import unittest

from pyramid import testing

from daybed.schemas import TypeRegistry, NotRegisteredError


class TypeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.types = TypeRegistry()

    def tearDown(self):
        testing.tearDown()

    def test_register(self):
        # Register a type
        self.assertEqual([], self.types.names)
        self.types.register('foo', None)
        self.assertEqual(['foo'], self.types.names)
        # Unregister unknown
        self.assertRaises(NotRegisteredError, self.types.unregister, 'bar')
        # Unregister the type
        self.types.unregister('foo')
        self.assertEqual([], self.types.names)
        # Unregister again
        self.assertRaises(NotRegisteredError, self.types.unregister, 'foo')
