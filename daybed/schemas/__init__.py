from pyramid.config import global_registries
from colander import (SchemaType, SchemaNode, Mapping, null, String,
                      OneOf, Boolean, Regex)

def get_db():
    return global_registries.last.backend


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

    def type(self, name):
        return self._registry[name]

registry = TypeRegistry()


class TypeField(object):
    node = String
    required = True
    default_value = null
    hint = u''

    @classmethod
    def definition(cls, **kwargs):
        schema = SchemaNode(Mapping(unknown="preserve"))

        if kwargs.get('named', True):
            schema.add(SchemaNode(String(), name='name',
                       validator=Regex(r'^[a-zA-Z][a-zA-Z0-9_\-]*$')))

        schema.add(SchemaNode(String(), name='label', missing=u''))
        schema.add(SchemaNode(String(), name='hint', missing=cls.hint))
        schema.add(SchemaNode(Boolean(), name='required',
                              missing=cls.required))
        schema.add(SchemaNode(String(), name='type',
                              validator=OneOf(registry.names)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        keys = ['name', 'label', 'hint', 'validator', 'missing']
        specified = [key for key in keys if key in kwargs.keys()]
        options = dict(zip(specified, [kwargs.get(k) for k in specified]))
        # If field is not required, use missing
        if not kwargs.get('required', cls.required):
            options.setdefault('missing', cls.default_value)
        return SchemaNode(cls.node(), **options)


class TypeFieldNode(SchemaType):
    def __init__(self, *args, **kwargs):
        super(TypeFieldNode, self).__init__()
        self.kwargs = kwargs

    def deserialize(self, node, cstruct=null):
        self.kwargs.update(node=node, cstruct=cstruct)
        try:
            schema = registry.definition(cstruct.get('type'), **self.kwargs)
        except UnknownFieldTypeError:
            schema = TypeField.definition(**self.kwargs)
        return schema.deserialize(cstruct)


from .base import *  # flake8: noqa
from .geom import *  # flake8: noqa
from .json import *  # flake8: noqa
from .relations import *  # flake8: noqa
from .object import *  # flake8: noqa
from .list import *  # flake8: noqa
