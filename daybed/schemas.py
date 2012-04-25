from colander import (
    SchemaNode,
    MappingSchema,
    Mapping,
    SequenceSchema,
    TupleSchema,
    String,
    Int,\
    OneOf,
    Length
)


class UnknownFieldTypeError(Exception):
    """ Raised if schema contains a field with unknown type. """
    pass


class ModelChoices(TupleSchema):
    choice = String()


class ModelField(MappingSchema):
    name = SchemaNode(String())
    type = SchemaNode(String(), validator=OneOf(('int', 'string', 'enum')))
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
            validator = None
            # TODO: implement a type registry (issue #2)
            if fieldtype == 'int':
                nodetype = Int()
            elif fieldtype == 'string':
                nodetype = String()
            elif fieldtype == 'enum':
                nodetype = String()
                validator = OneOf(field['choices'])
            else:
                raise UnknownFieldTypeError('Type "%s" is unknown' % fieldtype)
            self.add(SchemaNode(nodetype, name=field['name'],
                                description=field['description'],
                                validator=validator))
