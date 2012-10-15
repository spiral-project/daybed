import os
import json
from functools import partial

from pyramid.exceptions import NotFound
import colander
from cornice import Service
from cornice.util import json_error

from schemas import DefinitionValidator, SchemaValidator
from designdocs import db_model_token, db_model_definition, db_model_data


model_definition = Service(name='model_definition',
                           path='/definition/{modelname}',
                           description='Model Definition')

model_data = Service(name='model_data',
                     path='/{modelname}',
                     description='Model')


def validator(request, schema):
    """Validates the request according to the given schema"""
    try:
        body = request.body
        dictbody = json.loads(body) if body else {}
        schema.deserialize(dictbody)
    except ValueError, e:
        request.errors.add('body', 'body', str(e))
    except colander.Invalid, e:
        for error in e.children:
            # here we transform the errors we got from colander into cornice
            # errors
            for field, error in error.asdict().items():
                request.errors.add('body', field, error)


#  Validates a request body according model definition schema.
definition_validator = partial(validator, schema=DefinitionValidator())


def schema_validator(request):
    """Validates a request body according to its model definition.
    """
    definition = get_model_definition(request)  # TODO: appropriate ?
    schema = SchemaValidator(definition)
    return validator(request, schema)


@model_definition.put(validators=definition_validator)
def create_model_definition(request):
    """Create or update a model definition.

    Checks that the data is a valid model definition.
    In the case of a modification, checks that the token is valid and present.
    """
    modelname = request.matchdict['modelname']
    results = db_model_token(request.db)[modelname]
    tokens = [t.value for t in results]
    if len(tokens) > 0:
        token = tokens[0]
        if token != request.GET.get('token'):
            # provided token does not match
            request.errors.add('query', 'token',
                               'invalid token for model %s' % modelname)
            request.errors.status = 403
            return json_error(request.errors)
    else:
        # Generate a unique token
        token = os.urandom(8).encode('hex')
        token_doc = {'type': 'token', 'token': token, 'model': modelname}
        request.db.save(token_doc)

    model_doc = {
        'type': 'definition',
        'model': modelname,
        'definition': json.loads(request.body)
    }
    request.db.save(model_doc)
    return {'token': token}


@model_definition.get()
def get_model_definition(request):
    """Retrieves the model definition."""
    modelname = request.matchdict['modelname']
    results = db_model_definition(request.db)[modelname]
    for result in results:
        return result.value
    raise NotFound("Unknown model %s" % modelname)


@model_data.post(validators=schema_validator)
def post_model_data(request):
    """Saves a model record.

    Posted data fields will be matched against their related model
    definition.
    """
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
    """Retrieves all model records.
    """
    modelname = request.matchdict['modelname']
    # Check that model is defined
    exists = db_model_definition(request.db)[modelname]
    if not exists:
        raise NotFound("Unknown model %s" % modelname)
    # Return array of records
    results = db_model_data(request.db)[modelname]
    # TODO: should we transmit uuids or keep them secret for editing
    data = [result.value for result in results]
    return {'data': data}
