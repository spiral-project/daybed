import os

from cornice import Service
from colander import (
    MappingSchema,
    String,
    SequenceSchema,
    TupleSchema,
    SchemaNode,
    OneOf
)


class ModelChoices(TupleSchema):
    choice = String()


class ModelField(MappingSchema):
    name = SchemaNode(String())
    type = SchemaNode(String(), validator=OneOf(('int', 'string', 'enum')))
    description = SchemaNode(String())
    # TBD in subclassing, a way to have optional fields. Cross Field ?
    choices = ModelChoices()


class ModelFields(SequenceSchema):
    field = ModelField()


class ModelDefinition(MappingSchema):
    title = SchemaNode(String(), location="body")
    description = SchemaNode(String(), location="body")
    fields = ModelFields(location="body")


model_definition = Service(name='model_definition',
                           path='/definition/{modelname}',
                           description='Model Definition')

model = Service(name='model_data', path='/{modelname}', description='Model')


@model_definition.put(schema=ModelDefinition)
def create_model_definition(request):
    """Creates a model definition.

    In addition to checking that the data sent complies with what's expected
    (the schema), we check that, on case of an modification, the token is
    present and valid.
    """
    modelname = request.matchdict['modelname']
    token_uri = 'tokens/{modename}'.format(request.matchdict)
    token = request.db.get(token_uri)
    if token and token is not request.GET['token']:
        return request.errors.add('body', 'token',
                                  'the given token is not valid')
    else:
        # Generate a unique token
        token = request.db.put(token_uri, token=os.urandom(8).encode('hex'))

    request.db.put(uri=modelname, data=request.body)  # save to couchdb
    return {'token': token}
