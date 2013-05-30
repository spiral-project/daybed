import datetime

import pyramid.testing
import colander

from daybed import schemas
from daybed.schemas.base import (TypeRegistry, NotRegisteredError,
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
        self.assertEqual([], self.types.names)
        self.types.register('foo', None)
        self.assertEqual(['foo'], self.types.names)

    def test_unregister_unknown(self):
        # Unregister unknown
        self.assertRaises(NotRegisteredError,
                          self.types.unregister, 'foo')

    def test_unregister(self):
        self.types.register('bar', None)
        self.assertEqual(['bar'], self.types.names)
        self.types.unregister('bar')
        self.assertEqual([], self.types.names)
        self.assertRaises(UnknownFieldTypeError,
                          self.types.definition, 'bar')
        self.assertRaises(UnknownFieldTypeError,
                          self.types.validation, 'bar')

    def test_register_again(self):
        self.types.register('foo', None)
        self.assertRaises(AlreadyRegisteredError,
                          self.types.register, 'foo', None)

    def test_range(self):
        schema = schemas.RangeField.definition()
        definition = schema.deserialize(
            {'description': 'Some field',
             'name': 'age',
             'type': 'range',
             'min': 0, 'max': 100,})

        validator = schemas.RangeField.validation(**definition)
        self.assertEquals(30, validator.deserialize(30))
        self.assertRaises(colander.Invalid, validator.deserialize, -5)
        self.assertRaises(colander.Invalid, validator.deserialize, 120)

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

    def test_email(self):
        schema = schemas.EmailField.definition()
        definition = schema.deserialize(
            {'description': 'Some field',
             'name': 'address',
             'type': 'email'})

        validator = schemas.EmailField.validation(**definition)
        self.assertEquals('u@you.org', validator.deserialize('u@you.org'))
        self.assertEquals('u+i@you.org', validator.deserialize('u+i@you.org'))
        self.assertRaises(colander.Invalid, validator.deserialize, 'u i@you.org')

    def test_url(self):
        schema = schemas.URLField.definition()
        definition = schema.deserialize(
            {'description': 'Some field',
             'name': 'homepage',
             'type': 'url'})

        validator = schemas.URLField.validation(**definition)
        self.assertEquals('http://daybed.lolnet.org',
                          validator.deserialize('http://daybed.lolnet.org'))
        self.assertRaises(colander.Invalid, validator.deserialize, 'http://lolnet/org')

    def test_date(self):
        schema = schemas.DateField.definition()
        definition = schema.deserialize(
            {'description': 'First commit',
             'name': 'creation',
             'type': 'date'})

        validator = schemas.DateField.validation(**definition)
        self.assertEquals(datetime.date(2012, 4, 15),
                          validator.deserialize('2012-04-15'))
        self.assertRaises(colander.Invalid, validator.deserialize, '2012/04/15')
        self.assertRaises(colander.Invalid, validator.deserialize, '2012-13-01')
        self.assertRaises(colander.Invalid, validator.deserialize, '2012-04-31')
        self.assertRaises(colander.Invalid, validator.deserialize, '2012-04-30T13:37Z')

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
