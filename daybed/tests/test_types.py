import pyramid.testing
import colander

from daybed import schemas
from daybed.schemas.base import (TypeRegistry, NotRegisteredError,
                                 AlreadyRegisteredError)
from daybed.tests.support import unittest


class TypeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.types = TypeRegistry()

    def tearDown(self):
        pyramid.testing.tearDown()

    def test_register(self):
        # Register a type
        self.assertEqual([], self.types.names)
        self.types.register('foo', None)
        self.assertEqual(['foo'], self.types.names)

    def test_unregister_unknown(self):
        # Unregister unknown
        self.assertRaises(NotRegisteredError,
                          self.types.unregister, 'foo')

    def test_unregister(self):
        self.assertEqual([], self.types.names)

    def test_register_again(self):
        self.types.register('foo', None)
        self.assertRaises(AlreadyRegisteredError,
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

    def test_point(self):
        schema = schemas.PointField.definition()
        definition = schema.deserialize(
            {'description': 'Go',
             'name': 'location',
             'type': 'point'})

        validator = schemas.PointField.validation(**definition)
        self.assertEquals([0.4, 45.0], validator.deserialize('[0.4, 45.0]'))
        self.assertEquals([0, 45], validator.deserialize('[0, 45]'))
        self.assertEquals([0.4, 45.0, 1280], validator.deserialize('[0.4, 45.0, 1280]'))
        self.assertRaises(colander.Invalid, schema.deserialize, '[0.4]')
        self.assertRaises(colander.Invalid, schema.deserialize, '[[0.4, 45.0]]')
        self.assertRaises(colander.Invalid, schema.deserialize, '"0.4, 45.0"')
        self.assertRaises(colander.Invalid, schema.deserialize, '["a", "b"]')
        # Exceeding GPS coordinates
        self.assertRaises(colander.Invalid, schema.deserialize, '[181.0, 91.0]')
        self.assertRaises(colander.Invalid, schema.deserialize, '[-181.0, -91.0]')
        self.assertRaises(colander.Invalid, schema.deserialize, '[120.0, -91.0]')

    def test_point_euclidean(self):
        schema = schemas.PointField.definition()
        definition = schema.deserialize(
            {'description': 'Go',
             'name': 'location',
             'type': 'point',
             'gps': False})
        validator = schemas.PointField.validation(**definition)
        self.assertEquals([181.0, 91.0], validator.deserialize('[181.0, 91.0]'))

    def test_line(self):
        schema = schemas.LineField.definition()
        definition = schema.deserialize(
            {'description': 'Follow',
             'name': 'along',
             'type': 'line'})

        validator = schemas.LineField.validation(**definition)
        self.assertEquals([[0.4, 45.0], [0.6, 65.0]],
                          validator.deserialize('[[0.4, 45.0], [0.6, 65.0]]'))
        self.assertEquals([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                          validator.deserialize('[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]'))
        self.assertRaises(colander.Invalid, schema.deserialize, '[0.4, 45.0]')

    def test_polygon(self):
        schema = schemas.PolygonField.definition()
        definition = schema.deserialize(
            {'description': 'Scan',
             'name': 'area',
             'type': 'polygon'})

        validator = schemas.PolygonField.validation(**definition)
        # With linear-rings
        self.assertEquals([[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
                          validator.deserialize('[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]]'))
        # Check that non linear-rings are automatically closed
        self.assertEquals([[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
                          validator.deserialize('[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]]'))
        # With polygon hole
        self.assertEquals([[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]],
                           [[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
                          validator.deserialize("""[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                                                    [[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]]"""))
        self.assertRaises(colander.Invalid, schema.deserialize, '[[[0.4, 45.0]]]')
        self.assertRaises(colander.Invalid, schema.deserialize, '[[[0.4, 45.0], [0.6, 65.0]]]')
