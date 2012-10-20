import os
import json

from cornice import Service
from cornice.util import json_error
from pyramid.exceptions import NotFound

from daybed.validators import definition_validator


model_definition = Service(name='model_definition',
                           path='/definitions/{model_name}',
                           description='Model Definition',
                           renderer="jsonp")


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


