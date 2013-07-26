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


class FieldTypeTests(unittest.TestCase):
    def test_optional_description(self):
        schema = schemas.StringField.definition()
        definition = schema.deserialize(
            {'description': 'Some field',
             'name': 'address',
             'type': 'string'})
        self.assertEquals(definition.get('description'), 'Some field')
        # Description is optional (will not raise Invalid)
        definition = schema.deserialize(
            {'name': 'firstname',
             'type': 'string'})
        self.assertEquals(definition.get('description'), '')

    def test_optional_field(self):
        schema = schemas.IntField.definition()
        definition = schema.deserialize(
            {'name': 'address',
             'type': 'int'})
        validator = schemas.IntField.validation(**definition)
        self.assertRaises(colander.Invalid, validator.deserialize, '')

        definition = schema.deserialize(
            {'name': 'address',
             'type': 'int',
             'required': False})
        validator = schemas.IntField.validation(**definition)
        self.assertEquals(colander.null, validator.deserialize(''))
        self.assertRaises(colander.Invalid, validator.deserialize, 'abc')

    def test_range(self):
        schema = schemas.RangeField.definition()
        definition = schema.deserialize(
            {'name': 'age',
             'type': 'range',
             'min': 0, 'max': 100})

        validator = schemas.RangeField.validation(**definition)
        self.assertEquals(30, validator.deserialize(30))
        self.assertRaises(colander.Invalid, validator.deserialize, -5)
        self.assertRaises(colander.Invalid, validator.deserialize, 120)

    def test_regex(self):
        schema = schemas.RegexField.definition()
        definition = schema.deserialize(
            {'name': 'number',
             'type': 'regex',
             'regex': '\d+'})

        validator = schemas.RegexField.validation(**definition)
        self.assertEquals(1, int(validator.deserialize('1')))
        self.assertRaises(colander.Invalid, validator.deserialize, 'a')

    def test_email(self):
        schema = schemas.EmailField.definition()
        definition = schema.deserialize(
            {'name': 'address',
             'type': 'email'})

        validator = schemas.EmailField.validation(**definition)
        self.assertEquals('u@you.org', validator.deserialize('u@you.org'))
        self.assertEquals('u+i@you.org', validator.deserialize('u+i@you.org'))
        self.assertRaises(colander.Invalid, validator.deserialize, 'u i@you.org')

    def test_url(self):
        schema = schemas.URLField.definition()
        definition = schema.deserialize(
            {'name': 'homepage',
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
        self.assertRaises(colander.Invalid, validator.deserialize, '2012-04-31')  # April has 30 days only
        self.assertEquals(validator.deserialize('2012-04-30T13:37Z'),
                          datetime.date(2012, 4, 30))

    def test_datetime(self):
        schema = schemas.DateTimeField.definition()
        definition = schema.deserialize(
            {'description': 'First branch',
             'name': 'branch',
             'type': 'datetime'})

        validator = schemas.DateTimeField.validation(**definition)
        self.assertEquals(datetime.datetime(2012, 4, 16, 13, 45, 12, 0, colander.iso8601.UTC),
                          validator.deserialize('2012-04-16T13:45:12'))
        self.assertEquals(datetime.datetime(2012, 4, 16, 13, 45, 12, 0, colander.iso8601.UTC),
                          validator.deserialize('2012-04-16T13:45:12Z'))
        # Without time
        self.assertEquals(datetime.datetime(2012, 4, 16, 0, 0, 0, 0, colander.iso8601.UTC),
                          validator.deserialize('2012-04-16'))
        self.assertRaises(colander.Invalid, validator.deserialize, '2012/04/16 13H45')
        self.assertRaises(colander.Invalid, validator.deserialize, '2012-04-30T25:37Z')
        self.assertRaises(colander.Invalid, validator.deserialize, '2012-04-30T13:60Z')

    def test_datetime_auto_now(self):
        schema = schemas.DateTimeField.definition()
        definition = schema.deserialize(
            {'name': 'branch',
             'type': 'datetime',
             'auto_now': True})
        validator = schemas.DateTimeField.validation(**definition)
        defaulted = validator.deserialize(None)
        self.assertTrue((datetime.datetime.now() - defaulted).seconds < 1)
        defaulted = validator.deserialize('')
        self.assertTrue((datetime.datetime.now() - defaulted).seconds < 1)

    def test_datetime_optional_auto_now(self):
        schema = schemas.DateTimeField.definition()
        definition = schema.deserialize(
            {'name': 'branch',
             'type': 'datetime',
             'required': False})
        validator = schemas.DateTimeField.validation(**definition)
        self.assertEquals(colander.null, validator.deserialize(''))
        # If auto_now, defaulted value should be now(), not null
        definition = schema.deserialize(
            {'name': 'branch',
             'type': 'datetime',
             'required': False,
             'auto_now': True})
        validator = schemas.DateTimeField.validation(**definition)
        defaulted = validator.deserialize('')
        self.assertTrue((datetime.datetime.now() - defaulted).seconds < 1)

    def test_point(self):
        schema = schemas.PointField.definition()
        definition = schema.deserialize(
            {'name': 'location',
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
            {'name': 'location',
             'type': 'point',
             'gps': False})
        validator = schemas.PointField.validation(**definition)
        self.assertEquals([181.0, 91.0], validator.deserialize('[181.0, 91.0]'))

    def test_line(self):
        schema = schemas.LineField.definition()
        definition = schema.deserialize(
            {'name': 'along',
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
            {'name': 'area',
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
