import os
import json

from pyramid.exceptions import NotFound
from cornice import Service
from colander import (
    MappingSchema,
    String,
    SequenceSchema,
    TupleSchema,
    SchemaNode,
    OneOf,
    Length
)


class ModelChoices(TupleSchema):
    choice = String()


class ModelField(MappingSchema):
    name = SchemaNode(String())
    type = SchemaNode(String(), validator=OneOf(('int', 'string', 'enum')))
    description = SchemaNode(String())
    # TBD in subclassing, a way to have optional fields. Cross Field ?
    # choices = ModelChoices()


class ModelFields(SequenceSchema):
    field = ModelField()


class ModelDefinition(MappingSchema):
    title = SchemaNode(String(), location="body")
    description = SchemaNode(String(), location="body")
    fields = ModelFields(validator=Length(min=1), location="body")


model_definition = Service(name='model_definition', path='/definition/{modelname}', description='Model Definition')
model = Service(name='model_data', path='/{modelname}', description='Model')


@model_definition.put(schema=ModelDefinition)
def create_model_definition(request):
    """Creates a model definition.

    In addition to checking that the data sent complies with what's expected
    (the schema), we check that, on case of an modification, the token is
    present and valid.
    """
    modelname = request.matchdict['modelname']
    model_token = """function(doc) {
        if (doc.type == "token") {
            emit(doc.model, doc.token);
        }
    }"""  #TODO: permanent view
    results = request.db.query(model_token)[modelname]
    tokens = [t.value for t in results]
    
    if len(tokens) > 0:
        token = tokens[0]
        if token is not request.GET.get('token'):
            request.errors.add('query', 'token',
                               'the given token is not valid')
            raise  #TODO: cornice
    else:
        # Generate a unique token
        token = os.urandom(8).encode('hex')  #TODO: why not uuid?
        token_doc = {'type': 'token', 'token': token, 'model': modelname}
        request.db.save(token_doc)

    model_doc = {
        'type': 'definition',
        'model': modelname,
        'definition': json.loads(request.body)
    }
    request.db.save(model_doc)  # save to couchdb
    return {'token': token}


@model_definition.get()
def retrieve_model_definition(request):
    model_def = """function(doc) {
        if (doc.type == "definition") {
            emit(doc.model, doc.definition);
        }
    }"""  #TODO: permanent view
    modelname = request.matchdict['modelname']
    results = request.db.query(model_def)[modelname]

    for result in results:
        return result.value
    raise NotFound("Unknown model %s" % modelname)
