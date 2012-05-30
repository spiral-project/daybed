from colander import (
    SchemaNode,
    MappingSchema,
    Mapping,
    SequenceSchema,
    TupleSchema,
    String,
    Int,
    OneOf,
    Length
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
        if model not in self._registry:
            raise NotRegisteredError('The model %s is not registered' % name)
        del self._registry[name]

    def schema(self, typename, **options):
        try:
            nodetype = self._registry[typename]
        except KeyError:
            raise UnknownFieldTypeError('Type "%s" is unknown' % name)
        return nodetype(**options)

    @property
    def names(self):
        return self._registry.keys()


types = TypeRegistry()


class TypeField(SchemaNode):
    def __init__(self, node, **kwargs):
        options = dict(name='', 
                       description='',
                       validator=None)
        options.update(**kwargs)
        super(TypeField, self).__init__(node, **options)


class IntField(TypeField):
    def __init__(self, **kwargs):
        super(IntField, self).__init__(Int(), **kwargs)
types.register('int', IntField)


class StringField(TypeField):
    def __init__(self, **kwargs):
        super(StringField, self).__init__(String(), **kwargs)
types.register('string', StringField)


class EnumField(TypeField):
    def __init__(self, **kwargs):
        kwargs['validator'] = OneOf(kwargs['choices'])
        super(EnumField, self).__init__(String(), **kwargs)
types.register('enum', EnumField)


class ModelChoices(TupleSchema):
    choice = String()


class ModelField(MappingSchema):
    name = SchemaNode(String())
    type = SchemaNode(String(), validator=OneOf(types.names))
    description = SchemaNode(String())
    # TODO: TBD in subclassing, a way to have optional fields. Cross Field ?
    # choices = ModelChoices()


class ModelFields(SequenceSchema):
    field = ModelField()


class ModelDefinition(MappingSchema):
    title = SchemaNode(String(), location="body")
    description = SchemaNode(String(), location="body")
    fields = ModelFields(validator=Length(min=1), location="body")


class SchemaValidator(SchemaNode):
    def __init__(self, definition):
        super(SchemaValidator, self).__init__(Mapping())
        for field in definition['fields']:
            fieldtype = field['type']
            self.add(types.schema(fieldtype, **field))

