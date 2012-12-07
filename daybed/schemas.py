from colander import (
    SchemaNode,
    Mapping,
    Sequence,
    SchemaType,
    String,
    Boolean,
    Int,
    Float,
    OneOf,
    Range,
    Length,
    Regex,
    null,
    Invalid,
)


class AlreadyRegisteredError(Exception):
    pass


class NotRegisteredError(Exception):
    pass


class UnknownFieldTypeError(NotRegisteredError):
    """Raised if schema contains a field with an unknown type."""
    pass


class TypeRegistry(object):
    """Registry containing all the types.

    This can be extended by third parties, and is always imported from
    daybed.schemas.
    """

    def __init__(self):
        self._registry = {}

    def register(self, name, klass):
        if name in self._registry:
            raise AlreadyRegisteredError('The type %s is already registered' %
                                         name)
        self._registry[name] = klass

    def unregister(self, name):
        if name not in self._registry:
            raise NotRegisteredError('The model %s is not registered' % name)
        del self._registry[name]

    def validation(self, typename, **options):
        try:
            nodetype = self._registry[typename]
        except KeyError:
            raise UnknownFieldTypeError('Type "%s" is unknown' % typename)
        return nodetype.validation(**options)

    def definition(self, typename, **options):
        try:
            nodetype = self._registry[typename]
        except KeyError:
            raise UnknownFieldTypeError('Type "%s" is unknown' % typename)
        return nodetype.definition(**options)

    @property
    def names(self):
        return self._registry.keys()

    def add(self, name):
        """Decorator to register new types"""
        def decorated(cls):
            self.register(name, cls)
            return cls
        return decorated

registry = TypeRegistry()


class TypeField(object):
    node = String

    @classmethod
    def definition(cls):
        schema = SchemaNode(Mapping())
        schema.add(SchemaNode(String(), name='name'))
        schema.add(SchemaNode(String(), name='description'))
        schema.add(SchemaNode(String(), name='type',
                              validator=OneOf(registry.names)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        keys = ['name', 'description', 'validator']
        options = dict(zip(keys, [kwargs.get(k) for k in keys]))
        return SchemaNode(cls.node(), **options)


@registry.add('int')
class IntField(TypeField):
    node = Int


@registry.add('string')
class StringField(TypeField):
    node = String


@registry.add('enum')
class EnumField(TypeField):
    node = String

    @classmethod
    def definition(cls):
        schema = super(EnumField, cls).definition()
        schema.add(SchemaNode(Sequence(), SchemaNode(String()),
                              name='choices', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = OneOf(kwargs['choices'])
        return super(EnumField, cls).validation(**kwargs)


@registry.add('regex')
class RegexField(TypeField):
    """Allows to validate a field with a python regular expression."""
    node = String

    @classmethod
    def definition(cls):
        schema = super(RegexField, cls).definition()
        schema.add(SchemaNode(String(), name='regex', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Regex(kwargs['regex'])
        return super(RegexField, cls).validation(**kwargs)


class PointNode(SchemaNode):
    """Represents a position (x, y, z, ...)"""
    gps = True

    def __init__(self, *args, **kwargs):
        defaults = dict(validator=Length(min=2))
        defaults.update(**kwargs)
        super(PointNode, self).__init__(Sequence(), SchemaNode(Float()), **defaults)

    def deserialize(self, cstruct=null):
        deserialized = super(PointNode, self).deserialize(cstruct)
        longitude = Range(min=-180.0, max=180.0)
        latitude  = Range(min=-90.0, max=90.0)
        if self.gps:
            longitude(self, deserialized[0])
            latitude(self, deserialized[1])
        return deserialized


class PointType(SchemaType):
    gps = True

    def deserialize(self, node, cstruct=null):
        if cstruct is null:
            return null
        return PointNode(gps=self.gps).deserialize(cstruct)


class LinearRingNode(SchemaNode):
    gps = True

    def __init__(self, *args, **kwargs):
        defaults = dict(validator=Length(min=3))
        defaults.update(**kwargs)
        super(LinearRingNode, self).__init__(Sequence(), PointNode(gps=self.gps), **defaults)

    def deserialize(self, cstruct=null):
        deserialized = super(LinearRingNode, self).deserialize(cstruct)
        n = len(deserialized)
        # Add closing coordinates if not provided
        if n == 3 or deserialized[0][0] != deserialized[-1][0] or \
                     deserialized[0][1] != deserialized[-1][1]:
            deserialized.append(deserialized[0])
        return deserialized


class GeometryField(TypeField):
    """Base field for geometry values: basically a list of PointNode."""
    node = Sequence
    subnode = PointNode

    @classmethod
    def definition(cls):
        schema = super(GeometryField, cls).definition()
        schema.add(SchemaNode(Boolean(), name='gps', missing=True))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        validation = super(GeometryField, cls).validation(**kwargs)
        validation.add(cls.subnode(gps=kwargs['gps']))
        return validation


@registry.add('point')
class PointField(GeometryField):
    """A single position"""
    node = PointType

    @classmethod
    def validation(cls, **kwargs):
        validation = super(GeometryField, cls).validation(**kwargs)
        # Configure PointType from field definition
        validation.typ.gps = kwargs['gps']
        return validation


@registry.add('line')
class LineField(GeometryField):
    """At least two positions"""

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Length(min=2)
        validation = super(LineField, cls).validation(**kwargs)
        return validation


@registry.add('polygon')
class PolygonField(GeometryField):
    """At least three positions"""
    subnode = LinearRingNode


class TypeFieldNode(SchemaType):
    def deserialize(self, node, cstruct=null):
        try:
            schema = registry.definition(cstruct.get('type'))
        except UnknownFieldTypeError:
            schema = TypeField.definition()
        schema.deserialize(cstruct)


class DefinitionValidator(SchemaNode):
    def __init__(self):
        super(DefinitionValidator, self).__init__(Mapping())
        self.add(SchemaNode(String(), name='title'))
        self.add(SchemaNode(String(), name='description'))
        self.add(SchemaNode(Sequence(), SchemaNode(TypeFieldNode()),
                            name='fields', validator=Length(min=1)))


class SchemaValidator(SchemaNode):
    def __init__(self, definition):
        super(SchemaValidator, self).__init__(Mapping())
        for field in definition['fields']:
            fieldtype = field.pop('type')
            self.add(registry.validation(fieldtype, **field))
 