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

    def test_point_node(self):
        schema = schemas.PointNode()
        self.assertEquals([0.4, 45.0], schema.deserialize([0.4, 45.0]))
        self.assertEquals([0, 45], schema.deserialize([0, 45]))
        self.assertEquals([0.4, 45.0, 128], schema.deserialize([0.4, 45.0, 128]))
        self.assertRaises(colander.Invalid, schema.deserialize, [0.4])
        self.assertRaises(colander.Invalid, schema.deserialize, '"0.4, 45.0"')
        self.assertRaises(colander.Invalid, schema.deserialize, ["a", "b"])

    def test_coordinate_node(self):
        schema = schemas.PointNode(coordinate=False)
        self.assertEquals([181.0, 91.0], schema.deserialize([181.0, 91.0]))
        schema = schemas.PointNode()
        self.assertRaises(colander.Invalid, schema.deserialize, [181.0, 91.0])
        self.assertRaises(colander.Invalid, schema.deserialize, [-181.0, -91.0])
        self.assertRaises(colander.Invalid, schema.deserialize, [120.0, -91.0])
        self.assertEquals([0.4, 45.0, 181], schema.deserialize([0.4, 45.0, 181]))

    def test_point(self):
        schema = schemas.PointField.definition()
        definition = schema.deserialize(
            {'description': 'Go',
             'name': 'location',
             'type': 'point'})

        validator = schemas.PointField.validation(**definition)
        self.assertEquals([[0.4, 45.0]], validator.deserialize([[0.4, 45.0]]))
        self.assertRaises(colander.Invalid, schema.deserialize, [[0.4, 45.0],
                                                                 [0.6, 65.0]])

    def test_line(self):
        schema = schemas.LineField.definition()
        definition = schema.deserialize(
            {'description': 'Follow',
             'name': 'along',
             'type': 'line'})

        validator = schemas.LineField.validation(**definition)
        self.assertEquals([[0.4, 45.0], [0.6, 65.0]],
                          validator.deserialize([[0.4, 45.0], [0.6, 65.0]]))
        self.assertEquals([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                          validator.deserialize([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]))
        self.assertRaises(colander.Invalid, schema.deserialize, [0.4, 45.0])

    def test_polygon(self):
        schema = schemas.PolygonField.definition()
        definition = schema.deserialize(
            {'description': 'Scan',
             'name': 'area',
             'type': 'polygon'})

        validator = schemas.PolygonField.validation(**definition)
        self.assertEquals([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                          validator.deserialize([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]))
        self.assertRaises(colander.Invalid, schema.deserialize, [0.4, 45.0])
        self.assertRaises(colander.Invalid, schema.deserialize, [[0.4, 45.0], [0.6, 65.0]])
