import colander

from daybed import schemas
from daybed.tests.support import unittest


class PointFieldTests(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.PointField.definition()
        definition = self.schema.deserialize(
            {'name': 'location',
             'type': 'point'})
        self.validator = schemas.PointField.validation(**definition)

    def test_coordinates_as_float_or_integer(self):
        self.assertEquals([0.4, 45.0],
                          self.validator.deserialize('[0.4, 45.0]'))
        self.assertEquals([0, 45],
                          self.validator.deserialize('[0, 45]'))

    def test_with_third_coordinate(self):
        self.assertEquals([0.4, 45.0, 1280],
                          self.validator.deserialize('[0.4, 45.0, 1280]'))

    def test_fails_with_null_if_required(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, colander.null)

    def test_works_with_null_if_not_required(self):
        definition = self.schema.deserialize(
            {'name': 'location',
             'type': 'point',
             'required': 'false'})
        validator = schemas.PointField.validation(**definition)
        self.assertEquals(colander.null,
                          validator.deserialize(colander.null))

    def test_fails_with_invalid_json(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[0.4,,45.0]')

    def test_fails_with_invalid_coordinates(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[0.4]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[0.4, 45.0]]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '"0.4, 45.0"')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '["a", "b"]')

    def test_fails_with_coordinates_exceeding_earth(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[181.0, 91.0]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[-181.0, -91.0]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[120.0, -91.0]')


class EuclideanPointFieldTests(unittest.TestCase):
    def test_point_euclidean(self):
        schema = schemas.PointField.definition()
        definition = schema.deserialize(
            {'name': 'location',
             'type': 'point',
             'gps': False})
        validator = schemas.PointField.validation(**definition)
        self.assertEquals([181.0, 91.0],
                          validator.deserialize('[181.0, 91.0]'))


class LineFieldTests(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.LineField.definition()
        definition = self.schema.deserialize(
            {'name': 'along',
             'type': 'line'})
        self.validator = schemas.LineField.validation(**definition)

    def test_works_with_at_least_two_points(self):
        self.assertEquals([[0.4, 45.0], [0.6, 65.0]],
                          self.validator.deserialize(
                              '[[0.4, 45.0], [0.6, 65.0]]'))
        self.assertEquals([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                          self.validator.deserialize(
                              '[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]'))

    def test_fails_with_null_if_required(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, colander.null)

    def test_works_with_null_if_not_required(self):
        definition = self.schema.deserialize(
            {'name': 'along',
             'type': 'line',
             'required': 'false'})
        validator = schemas.LineField.validation(**definition)
        self.assertEquals(colander.null,
                          validator.deserialize(colander.null))

    def test_fails_with_one_point(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[0.4, 45.0]]')

    def test_fails_if_not_a_list(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[0.4, 45.0]')

    def test_fails_with_invalid_json(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[4,4],[4,,5]]')


class PolygonFieldTests(unittest.TestCase):
    def setUp(self):
        schema = schemas.PolygonField.definition()
        definition = schema.deserialize(
            {'name': 'area',
             'type': 'polygon'})
        self.validator = schemas.PolygonField.validation(**definition)

    def test_works_with_a_linear_ring(self):
        self.assertEquals(
            [[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
            self.validator.deserialize(
                '[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]]'))

    def test_non_linear_ring_are_automatically_closed(self):
        self.assertEquals(
            [[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
            self.validator.deserialize(
                '[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]]'))

    def test_works_with_hole_in_polygon(self):
        self.assertEquals(
            [[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]],
             [[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
            self.validator.deserialize(
                """[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                   [[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]]"""))

    def test_fails_if_not_enough_points(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[[0.4, 45.0]]]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '[[[0.4, 45.0], [0.6, 65.0]]]')
