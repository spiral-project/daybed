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

    def test_deserialization_is_idempotent(self):
        self.assertEquals([0.4, 45.0],
                          self.validator.deserialize([0.4, 45.0]))

    def test_coordinates_are_deserialized_as_float_or_integer(self):
        self.assertEquals([0.4, 45.0],
                          self.validator.deserialize('[0.4, 45.0]'))
        self.assertEquals([0, 45],
                          self.validator.deserialize('[0, 45]'))

    def test_coordinates_can_have_several_dimensions(self):
        self.assertEquals([0.4, 45.0, 1280],
                          self.validator.deserialize('[0.4, 45.0, 1280]'))
        self.assertEquals([0.4, 45.0, 1280, 2048],
                          self.validator.deserialize(
                              '[0.4, 45.0, 1280, 2048]'))

    def test_coordinates_cannot_be_null_if_required(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, colander.null)

    def test_coordinates_can_be_null_if_not_required(self):
        definition = self.schema.deserialize(
            {'name': 'location',
             'type': 'point',
             'required': 'false'})
        validator = schemas.PointField.validation(**definition)
        self.assertEquals(colander.null,
                          validator.deserialize(colander.null))

    def test_coordinates_must_be_valid_json(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[0.4,,45.0]')

    def test_coordinates_cannot_be_invalid_data(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[0.4]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[0.4, 45.0]]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '"0.4, 45.0"')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '["a", "b"]')

    def test_coordinates_cannot_exceed_earth(self):
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

    def test_lines_have_at_least_two_points(self):
        self.assertEquals([[0.4, 45.0], [0.6, 65.0]],
                          self.validator.deserialize(
                              '[[0.4, 45.0], [0.6, 65.0]]'))
        self.assertEquals([[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                          self.validator.deserialize(
                              '[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]'))

    def test_lines_cannot_be_null_if_required(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, colander.null)

    def test_lines_can_be_null_if_not_required(self):
        definition = self.schema.deserialize(
            {'name': 'along',
             'type': 'line',
             'required': 'false'})
        validator = schemas.LineField.validation(**definition)
        self.assertEquals(colander.null,
                          validator.deserialize(colander.null))

    def test_lines_must_have_at_least_two_points(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[0.4, 45.0]]')

    def test_lines_must_be_a_list_of_coordinates(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[0.4, 45.0]')

    def test_lines_must_be_valid_json(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[4,4],[4,,5]]')


class PolygonFieldTests(unittest.TestCase):
    def setUp(self):
        schema = schemas.PolygonField.definition()
        definition = schema.deserialize(
            {'name': 'area',
             'type': 'polygon'})
        self.validator = schemas.PolygonField.validation(**definition)

    def test_polygones_are_linear_ring(self):
        self.assertEquals(
            [[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
            self.validator.deserialize(
                '[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]]'))

    def test_polygones_are_automatically_closed(self):
        self.assertEquals(
            [[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
            self.validator.deserialize(
                '[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]]'))

    def test_polygones_can_have_holes(self):
        self.assertEquals(
            [[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]],
             [[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]],
            self.validator.deserialize(
                """[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]],
                   [[0.4, 45.0], [0.6, 65.0], [0.8, 85.0]]]"""))

    def test_polygones_must_have_enough_points(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '[[[0.4, 45.0]]]')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '[[[0.4, 45.0], [0.6, 65.0]]]')


class GeoJSONFieldTests(unittest.TestCase):
    def setUp(self):
        schema = schemas.GeoJSONField.definition()
        definition = schema.deserialize(
            {'name': 'webmap',
             'type': 'geojson'})
        self.validator = schemas.GeoJSONField.validation(**definition)

    def test_geojson_is_json_with_type_and_coordinates(self):
        deserialized = self.validator.deserialize("""
           {"type": "Point",
            "coordinates": [100.0, 0.0] }""")
        self.assertDictEqual({"type": "Point",
                              "coordinates": [100.0, 0.0]}, deserialized)

    def test_geojson_can_be_a_collection(self):
        deserialized = self.validator.deserialize("""
           {"type": "GeometryCollection",
            "geometries": [{"type": "Point",
                            "coordinates": [100.0, 0.0] }]}""")
        self.assertDictEqual({"type": "Point",
                              "coordinates": [100.0, 0.0]},
                             deserialized['geometries'][0])

    def test_geojson_must_have_type(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '{"coordinates": [1, 2] }')
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '{"type": null, "coordinates": [1, 2] }')

    def test_geojson_cannot_have_unknown_type(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          '{"type": "Triangle", "coordinates": [1, 2] }')

    def test_geojson_collection_items_cannot_have_unknown_type(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          """{"type": "GeometryCollection",
                              "geometries": [{"type": "Triangle",
                                              "coordinates": [1, 0] }]}""")

    def test_geojson_collection_must_have_geometries(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize,
                          """{"type": "GeometryCollection"}""")

    def test_geojson_collection_can_be_empty(self):
        deserialized = self.validator.deserialize("""
            {"type": "GeometryCollection",
             "geometries": []}""")
        self.assertDictEqual({"type": "GeometryCollection",
                              "geometries": []},
                             deserialized)
