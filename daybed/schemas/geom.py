from __future__ import absolute_import
import json

import six
from colander import (
    SchemaNode,
    Sequence,
    Length,
    SchemaType,
    Boolean,
    Float,
    Range,
    null,
    Invalid,
    OneOf
)

from .base import registry, TypeField
from .json import JSONSequence, JSONType, JSONField, JSONList


__all__ = ['PointField', 'LineField', 'PolygonField', 'GeoJSONField']


class PointNode(SchemaNode):
    """A node representing a position (x, y, z, ...)"""
    gps = True

    def __init__(self, *args, **kwargs):
        defaults = dict(validator=Length(min=2))
        defaults.update(**kwargs)
        super(PointNode, self).__init__(Sequence(),
                                        SchemaNode(Float()), **defaults)

    def deserialize(self, cstruct=null):
        deserialized = super(PointNode, self).deserialize(cstruct)
        longitude = Range(min=-180.0, max=180.0)
        latitude = Range(min=-90.0, max=90.0)
        if self.gps:
            longitude(self, deserialized[0])
            latitude(self, deserialized[1])
        return deserialized


class PointType(SchemaType):
    """A schema type dedicated to ``PointNode`` in JSON-like format"""
    gps = True

    def deserialize(self, node, cstruct=null):
        if cstruct is null:
            return null
        try:
            appstruct = cstruct
            if isinstance(cstruct, six.string_types):
                appstruct = json.loads(cstruct)
        except ValueError as e:
            raise Invalid(node, six.text_type(e), cstruct)
        return PointNode(name=node.name, gps=self.gps).deserialize(appstruct)


class LinearRingNode(SchemaNode):
    """A node representing a linear-ring.

    A ring is defined from at least three ``PointNode``. If the ring
    is not closed (i.e. last point differs from first) an additionnal
    point will added during serialization.
    """
    gps = True

    def __init__(self, *args, **kwargs):
        defaults = dict(validator=Length(min=3))
        defaults.update(**kwargs)
        super(LinearRingNode, self).__init__(Sequence(),
                                             PointNode(gps=self.gps),
                                             **defaults)

    def deserialize(self, cstruct=null):
        deserialized = super(LinearRingNode, self).deserialize(cstruct)
        n = len(deserialized)
        # Add closing coordinates if not provided
        if n == 3 or deserialized[0] != deserialized[-1]:
            deserialized.append(deserialized[0])
        return deserialized


class GeometryField(TypeField):
    """A field type representing geometries: basically a list of positions.

    Positions are coordinates following *x, y, z* order
    (or *longitude, latitude, altitude*) for geographic coordinates).
    A minimum of two dimensions is required,
    but any number of additional elements are allowed.

    This field definition accepts one optional parameter:

    ``gps``
       If ``True``, coordinates must be in the range of GPS coordinates
       system (WGS84), basically ``x`` in [-180, +180] and ``y`` in
       [-90, +90].
    """
    gps = True

    node = JSONSequence
    subnode = PointNode

    @classmethod
    def definition(cls):
        schema = super(GeometryField, cls).definition()
        schema.add(SchemaNode(Boolean(), name='gps', missing=cls.gps))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        validation = super(GeometryField, cls).validation(**kwargs)
        validation.add(cls.subnode(gps=kwargs.get('gps', cls.gps)))
        return validation


@registry.add('point')
class PointField(GeometryField):
    """A field representing a single position
    :ref:`GeometryField`
    """
    node = PointType

    @classmethod
    def validation(cls, **kwargs):
        validation = super(GeometryField, cls).validation(**kwargs)
        # Configure PointType from field definition
        validation.typ.gps = kwargs.get('gps', cls.node.gps)
        return validation


@registry.add('line')
class LineField(GeometryField):
    """A field representing a line, of at least two positions.
    :ref:`GeometryField`
    """

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Length(min=2)
        validation = super(LineField, cls).validation(**kwargs)
        return validation


@registry.add('polygon')
class PolygonField(GeometryField):
    """A field representing a polygon and its optional holes.

    A polygon is a list of linear rings. The first represents the
    envelop (exterior), and the following one (optional) its holes.

    A linear-ring is a closed line : basically a list of positions,
    where the first and last items are equal.

    :ref:`GeometryField`
    """
    subnode = LinearRingNode


class GeoJSONType(JSONType):
    """This JSON follows a specific profile : GeoJSON (http://geojson.org).

    According to the type of geometry provided, we check the coordinates
    validity, using the deserializers implemented for ``GeometryField``.

    :note:

        This field does not accept ``Feature`` and ``FeatureCollection`` yet.
    """
    def deserialize(self, node, cstruct=null):
        appstruct = super(GeoJSONType, self).deserialize(node, cstruct)

        geom_type = appstruct.get('type')
        self._check_geom_type(node, geom_type)

        if geom_type == 'GeometryCollection':
            geometries = appstruct.get('geometries')
            self._check_collection(node, geometries)
        else:
            coordinates = appstruct.get('coordinates')
            self._check_coordinates(node, geom_type, coordinates)
        return appstruct

    def _check_geom_type(self, node, geom_type):
        geom_types = ('Point', 'LineString', 'Polygon', 'GeometryCollection',
                      'MultiPoint', 'MultiLineString', 'MultiPolygon')
        OneOf(geom_types)(node, geom_type)

    def _check_collection(self, node, geometries):
        subnodes = JSONList().deserialize(node, geometries)
        for subnode in subnodes:
            GeoJSONType().deserialize(node, subnode)

    def _check_coordinates(self, node, geom_type, coordinates):
        serializers = {
            'Point': PointNode(gps=False),
            'LineString': SchemaNode(Sequence(), PointNode(gps=False)),
            'Polygon': SchemaNode(Sequence(), LinearRingNode(gps=False))
        }
        single_serializers = [kv for kv in serializers.items()]
        for singletype, serializer in single_serializers:
            multitype = 'Multi' + singletype
            serializers[multitype] = SchemaNode(Sequence(), serializer)
        # Match coordinates by type. Can raise ``colander.Invalid``
        serializers[geom_type].deserialize(coordinates)


@registry.add('geojson')
class GeoJSONField(JSONField):
    node = GeoJSONType
