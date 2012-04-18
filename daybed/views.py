import os

from cornice import Service
from colander import (
    MappingSchema,
    String,
    ModelField,
    SequenceSchema,
    SchemaNode,
    OneOf
)


class ModelDefinition(MappingSchema):
    title = SchemaNode(String())
    description = SchemaNode(String())
    fields = SequenceSchema(ModelField())


class ModelField(MappingSchema):
    name = SchemaNode(String())
    type = SchemaNode(String(), validator=OneOf(('int', 'string', 'enum')))
    description = SchemaNode(String())
    # TBD in subclassing, a way to have optional fields. Cross Field ?
    choices = SequenceSchema(String())


model_definition = Service('Model Definition', '/definition/{modelname}')
model = Service('Model', '/{modelname}')


@model_definition.PUT(schema=ModelDefinition())
def create_model_definition(request):
    """Creates a model definition.

    In addition to checking that the data sent complies with what's expected
    (the schema), we check that, on case of an modification, the token is
    present and valid.
    """
    con = couchdb.get_connection()
    modelname = request.matchdict['modelname']
    token_uri = 'tokens/{modename}'.format(request.matchdict)
    token = con.get(token_uri)
    if token and token is not request.GET['token']:
        return request.errors.add('body', 'token',
                                  'the given token is not valid')
    else:
        # Generate a unique token
        token = con.put(token_uri, token=os.urandom(8).encode('hex'))

    con.put(uri=modelname, data=request.body)  # save to couchdb
    return {'token': token}
