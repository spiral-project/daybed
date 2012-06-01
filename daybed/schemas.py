from colander import (
    SchemaNode,
    Mapping,
    Sequence,
    SchemaType,
    Tuple,
    String,
    Int,
    OneOf,
    Length,
    null,
    Invalid,
    _
)


class AlreadyRegisteredError(Exception):
    pass


class NotRegisteredError(Exception):
    pass


class UnknownFieldTypeError(NotRegisteredError):
    """ Raised if schema contains a field with unknown type. """
    pass


class TypeRegistry(object):
    def __init__(self):
        self._registry = {}

    def register(self, name, klass):
        if name in self._registry:
            raise AlreadyRegisteredError('The type %s is already registered' % name)
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

types = TypeRegistry()


class TypeField(object):
    node = String

    @classmethod
    def definition(cls):
        schema = SchemaNode(Mapping())
        schema.add(SchemaNode(String(), name='name'))
        schema.add(SchemaNode(String(), name='description'))
        schema.add(SchemaNode(String(), name='type',
                              validator=OneOf(types.names)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        keys = ['name', 'description', 'validator']
        options = dict(zip(keys, [kwargs.get(k) for k in keys]))
        return SchemaNode(cls.node(), **options)


class IntField(TypeField):
    node = Int
types.register('int', IntField)


class StringField(TypeField):
    node = String
types.register('string', StringField)


class EnumField(TypeField):
    node = String

    @classmethod
    def definition(cls):
        schema = super(EnumField, cls).definition()
        schema.add(SchemaNode(Tuple(), SchemaNode(String()), name='choices'))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = OneOf(kwargs['choices'])
        super(EnumField, cls).validation(**kwargs)
types.register('enum', EnumField)



class TypeFieldNode(SchemaType):
    def deserialize(self, node, cstruct=null):
        try:
            schema = types.definition(cstruct.get('type'))
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
            self.add(types.validation(fieldtype, **field))
