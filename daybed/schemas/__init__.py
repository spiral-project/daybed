from colander import (SchemaType, SchemaNode, Mapping, null, String,
                      OneOf, Boolean)


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
            error_msg = 'The type %s is already registered (%s)' % (name,
                                                                    self._registry[name])
            raise AlreadyRegisteredError(error_msg)
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


from .base import *  # flake8: noqa
from .geom import *  # flake8: noqa
from .jayson import *  # flake8: noqa
from .relations import *  # flake8: noqa
