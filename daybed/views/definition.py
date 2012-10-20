import os
import json

from cornice import Service
from cornice.util import json_error
from pyramid.exceptions import NotFound

from daybed.validators import definition_validator, token_validator


definition = Service(name='definition',
                           path='/definitions/{model_name}',
                           description='Model Definition',
                           renderer="jsonp")


@definition.get()
def get(request):
    """Retrieves the model definition."""
    model_name = request.matchdict['model_name']
    definition = request.db.get_definition(model_name)
    if definition:
        return definition
    raise NotFound("Unknown model %s" % model_name)


@definition.put(validators=(token_validator, definition_validator))
def put(request):
    """Create or update a model definition.

    Checks that the data is a valid model definition.
    In the case of a modification, checks that the token is valid and present.

    """
    model_name = request.matchdict['model_name']

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
