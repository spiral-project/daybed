import os
import json

from pyramid.exceptions import NotFound
from cornice import Service
from cornice.util import json_error

from daybed.validators import definition_validator, schema_validator


model_definition = Service(name='model_definition',
                           path='/definitions/{model_name}',
                           description='Model Definition')

model_data = Service(name='model_data',
                     path='/{model_name}',
                     description='Model')


@model_definition.put(validators=definition_validator)
def create_model_definition(request):
    """Create or update a model definition.

    Checks that the data is a valid model definition.
    In the case of a modification, checks that the token is valid and present.
    """
    model_name = request.matchdict['model_name']
    results = request.db.get_definition_token(model_name)
    tokens = [t.value for t in results]
    if len(tokens) > 0:
        token = tokens[0]
        if token != request.GET.get('token'):
            # provided token does not match
            request.errors.add('query', 'token',
                               'invalid token for model %s' % model_name)
            request.errors.status = 403
            return json_error(request.errors)
    else:
        # Generate a unique token
        token = os.urandom(40).encode('hex')

    model_doc = {
        'type': 'definition',
        'name': model_name,
        'definition': json.loads(request.body),
        'token': token,
    }
    request.db.save(model_doc)
    return {'token': token}


@model_definition.get()
def get_model_definition(request):
    """Retrieves the model definition."""
    model_name = request.matchdict['model_name']
    definition = request.db.get_model_definition(model_name)
    if definition:
        return definition
    raise NotFound("Unknown model %s" % model_name)


@model_data.post(validators=schema_validator)
def post_model_data(request):
    """Saves a model record.

    Posted data fields will be matched against their related model
    definition.
    """
    model_name = request.matchdict['model_name']
    data_doc = {
        'type': 'data',
        'model_name': model_name,
        'data': json.loads(request.body)
    }
    _id, rev = request.db.save(data_doc)
    return {'id': _id}


@model_data.get()
def get_model_data(request):
    """Retrieves all model records.
    """
    model_name = request.matchdict['model_name']
    # Check that model is defined
    exists = request.db.get_model_definition(model_name)
    if not exists:
        raise NotFound("Unknown model %s" % model_name)
    # Return array of records
    results = request.db.get_model_data(model_name)
    # TODO: should we transmit uuids or keep them secret for editing
    data = [result.value for result in results]
    return {'data': data}
