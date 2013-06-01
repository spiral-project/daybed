import os
import json

from cornice import Service

from daybed.validators import definition_validator


definition_collection = Service(name='definition_collection',
                                path='/definitions/',
                                description='Model Definition Collection',
                                renderer="jsonp")


@definition_collection.post(validators=definition_validator)
def post(request):
    """Create a model definition.

    Checks that the data is a valid model definition.

    """
    model_name = request.registry.generate_model_name(request)

    # Generate a unique token
    token = os.urandom(40).encode('hex')

    model_doc = {
        'type': 'definition',
        'name': model_name,
        'definition': json.loads(request.body),
        'token': token,
    }
    request.db.save(model_doc)
    created = '%s/definitions/%s' % (request.application_url, model_name)
    request.response.status = "201 Created"
    request.response.headers['location'] = created
    return {'token': token, 'name': model_name}
