import mock
import colander
import pyramid.testing

from daybed.schemas import (TypeRegistry, NotRegisteredError,
                            TypeField, TypeFieldNode, registry,
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


class TypeFieldNodeTests(unittest.TestCase):
    def setUp(self):
        class FooField(TypeField):
            @classmethod
            def definition(self, **kwargs):
                mocked = mock.Mock()
                mocked.deserialize.return_value = 'blah'
                return mocked

        registry.register('foo', FooField)

    def tearDown(self):
        registry.unregister('foo')

    def test_node_returns_definition(self):
        fieldnode = TypeFieldNode()
        self.assertEqual('blah', fieldnode.deserialize(None, {'type': 'foo'}))

    def test_unknown_type_is_invalid(self):
        fieldnode = TypeFieldNode()
        self.assertRaises(colander.Invalid,
                          fieldnode.deserialize, None, {'type': 'unk'})
