import os
import json

from pyramid.exceptions import NotFound, Forbidden
from cornice import Service
import colander

from schemas import ModelDefinition, SchemaValidator


model_definition = Service(name='model_definition',
                           path='/definition/{modelname}',
                           description='Model Definition')

model_data = Service(name='model_data',
                     path='/{modelname}',
                     description='Model')


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
    }"""  # TODO: permanent view
    results = request.db.query(model_token)[modelname]
    tokens = [t.value for t in results]
    if len(tokens) > 0:
        token = tokens[0]
        if token != request.GET.get('token'):
            # TODO : return instead of raise ?
            #request.errors.add('query', 'token',
            #                   'the given token is not valid')
            raise Forbidden("Invalid token for model %s" % modelname)
    else:
        # Generate a unique token
        token = os.urandom(8).encode('hex')  # TODO: why not uuid?
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
def get_model_definition(request):
    model_def = """function(doc) {
        if (doc.type == "definition") {
            emit(doc.model, doc.definition);
        }
    }"""  # TODO: permanent view
    modelname = request.matchdict['modelname']
    results = request.db.query(model_def)[modelname]
    for result in results:
        return result.value
    raise NotFound("Unknown model %s" % modelname)


def schema_validator(request):
    definition = get_model_definition(request)  # TODO: appropriate ?
    validator = SchemaValidator(definition)
    try:
        validator.deserialize(json.loads(request.body))
    except colander.Invalid, e:
        for error in e.children:
            for field, error in error.asdict().items():
                request.errors.add('body', field, error)


@model_data.post(validators=schema_validator)
def post_model_data(request):
    modelname = request.matchdict['modelname']
    data_doc = {
        'type': 'data',
        'model': modelname,
        'data': json.loads(request.body)
    }
    _id, rev = request.db.save(data_doc)
    return {'id': _id}


@model_data.get()
def get_model_data(request):
    modelname = request.matchdict['modelname']
    model_data = """function(doc) {
        if (doc.type == "data") {
            emit(doc.model, doc.data);
        }
    }"""  # TODO: permanent view
    results = request.db.query(model_data)[modelname]
    # TODO: should we transmit uuids or keep them secret for editing
    data = [result['value'] for result in results]
    return {'data': data}
