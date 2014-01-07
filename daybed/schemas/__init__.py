from colander import (SchemaType, SchemaNode, Mapping, null, String,
                      Sequence, Length, Boolean, OneOf, Int, Range)


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
        """Class decorator, to register new types"""
        def decorated(cls):
            self.register(name, cls)
            return cls
        return decorated

registry = TypeRegistry()


class TypeField(object):
    node = String
    required = True
    default_value = null

    @classmethod
    def definition(cls):
        schema = SchemaNode(Mapping())
        schema.add(SchemaNode(String(), name='name'))
        schema.add(SchemaNode(String(), name='description', missing=''))
        schema.add(SchemaNode(Boolean(), name='required',
                              missing=cls.required))
        schema.add(SchemaNode(String(), name='type',
                              validator=OneOf(registry.names)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        keys = ['name', 'description', 'validator', 'missing']
        specified = [key for key in keys if key in kwargs.keys()]
        options = dict(zip(specified, [kwargs.get(k) for k in specified]))
        # If field is not required, use missing
        if not kwargs.get('required', cls.required):
            options.setdefault('missing', cls.default_value)
        return SchemaNode(cls.node(), **options)


class TypeFieldNode(SchemaType):
    def deserialize(self, node, cstruct=null):
        try:
            schema = registry.definition(cstruct.get('type'))
        except UnknownFieldTypeError:
            schema = TypeField.definition()
        return schema.deserialize(cstruct)


class DefinitionValidator(SchemaNode):
    def __init__(self):
        super(DefinitionValidator, self).__init__(Mapping())
        self.add(SchemaNode(String(), name='title'))
        self.add(SchemaNode(String(), name='description'))
        self.add(SchemaNode(Sequence(), SchemaNode(TypeFieldNode()),
                            name='fields', validator=Length(min=1)))


class RolesValidator(SchemaNode):
    def __init__(self):
        super(RolesValidator, self).__init__(Mapping(unknown='preserve'))
        self.add(SchemaNode(Sequence(), SchemaNode(String()),
                            name='admins', validator=Length(min=1)))

        # XXX Control that the values of the sequence are valid users.
        # (we need to merge master to fix this. see #86)


class PolicyValidator(SchemaNode):
    def __init__(self, policy):
        super(PolicyValidator, self).__init__(Mapping(unknown='preserve'))
        for key in six.iterkeys(policy):
            self.add(SchemaNode(Int(), name=key,
                                validator=Range(min=0, max=0xFFFF)))


class RecordValidator(SchemaNode):
    def __init__(self, definition):
        super(RecordValidator, self).__init__(Mapping())
        for field in definition['fields']:
            fieldtype = field.pop('type')
            self.add(registry.validation(fieldtype, **field))


from .base import *  # flake8: noqa
from .geom import *  # flake8: noqa
from .relations import *  # flake8: noqa
