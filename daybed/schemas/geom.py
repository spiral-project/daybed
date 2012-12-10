import json

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
)

from .base import registry, TypeField


__all__ = ['PointField', 'LineField', 'PolygonField']


class JSONSequence(Sequence):
    """A sequence of items in JSON-like format"""
    def deserialize(self, node, cstruct, **kwargs):
        if cstruct is null:
            return cstruct
        try:
            appstruct = json.loads(cstruct)
        except ValueError, e:
            raise Invalid(self, e, cstruct)
        return super(JSONSequence, self).deserialize(node, appstruct, **kwargs)


class PointNode(SchemaNode):
    """A node representing a position (x, y, z, ...)"""
    gps = True

    def __init__(self, *args, **kwargs):
        defaults = dict(validator=Length(min=2))
        defaults.update(**kwargs)
        super(PointNode, self).__init__(Sequence(), SchemaNode(Float()), **defaults)

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
            appstruct = json.loads(cstruct)
        except ValueError, e:
            raise Invalid(self, e, cstruct)
        return PointNode(gps=self.gps).deserialize(appstruct)


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
        super(LinearRingNode, self).__init__(
            Sequence(), PointNode(gps=self.gps), **defaults)

    def deserialize(self, cstruct=null):
        deserialized = super(LinearRingNode, self).deserialize(cstruct)
        n = len(deserialized)
        # Add closing coordinates if not provided
        if n == 3 or deserialized[0] != deserialized[-1]:
            deserialized.append(deserialized[0])
        return deserialized


class GeometryField(TypeField):
    """A field type representing geometries: basically a list of positions.

    Positions are coordinates following *x, y, z* order (or *longitude, latitude,
    altitude*) for geographic coordinates). A minimum of two dimensions is required,
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
        validation.typ.gps = kwargs['gps']
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
