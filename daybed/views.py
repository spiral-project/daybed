import os
import json

from pyramid.exceptions import NotFound
from cornice import Service
from cornice.util import json_error

from daybed.validators import definition_validator, schema_validator


model_definition = Service(name='model_definition',
                           path='/definitions/{modelname}',
                           description='Model Definition')

model_data = Service(name='model_data',
                     path='/{modelname}',
                     description='Model')


@model_definition.put(validators=definition_validator)
def create_model_definition(request):
    """Create or update a model definition.

    Checks that the data is a valid model definition.
    In the case of a modification, checks that the token is valid and present.
    """
    modelname = request.matchdict['modelname']
    results = request.db.get_definition_token(modelname)
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
        token = os.urandom(40).encode('hex')
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
    definition = request.db.get_model_definition(modelname)
    if definition:
        return definition
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
    exists = request.db.get_model_definition(modelname)
    if not exists:
        raise NotFound("Unknown model %s" % modelname)
    # Return array of records
    results = request.db.get_model_data(modelname)
    # TODO: should we transmit uuids or keep them secret for editing
    data = [result.value for result in results]
    return {'data': data}
