import json

from cornice import Service

from daybed.validators import validate_against_schema
from daybed.schemas import DefinitionValidator, SchemaValidator

models = Service(name='models', path='/models', description='Models',
                 renderer="jsonp", cors_origins=('*',))

model = Service(name='model', path='/models/{model_id}', description='Model',
                renderer="jsonp", cors_origins=('*',))


def model_validator(request):
    """Verify that the model is okay (that we have the right fields) and
    eventually populates it if there is a need to.
    """
    body = json.loads(request.body)

    # Check the definition is valid.
    definition = body.get('definition')
    if not definition:
        request.errors.add('body', 'definition', 'definition is required')
    else:
        validate_against_schema(request, DefinitionValidator(), definition)
    request.validated['definition'] = definition

    # Check that the data items are valid according to the definition.
    data = body.get('data')
    request.validated['data'] = []
    if data:
        definition_validator = SchemaValidator(definition)
        for data_item in data:
            validate_against_schema(request, definition_validator, data_item)
            request.validated['data'].append(data_item)

    return 
    # Check that users are valid users
    users = body.get('users', default_users)
    validate_against_schema(request, UserValidator(), users)
    request.validated['users'] = users

    policy_id = body.get('policy_id')


@models.post(validators=(model_validator,), permission='post_model')
def post_models(request):
    """creates an model with the given definition and data, if any."""
    model_id = request.db.put_model(definition=request.validated['definition'],
            users={'admins': ['group:admins'],
                   'authors': [request.validated['users']]},
                                    policy_id=request.validated['policy_id'])

    for data_item in request.validated['data']:
        request.db.put_data_item(model_id, data_item)

    request.response.status = "201 Created"
    location = '%s/models/%s' % (request.application_url, model_id)
    request.response.headers['location'] = location
    return {'id': model_id}


@model.delete(permission='delete_model')
def delete_model(request):
    """Deletes a model and its matching associated data."""
    model_id = request.matchdict['model_id']
    request.db.delete_model(model_id)
    return "ok"


@model.get(permission='get_model')
def get_model(request):
    """Returns the definition and data of the given model"""
    model_id = request.matchdict['model_id']

    return {'definition': request.db.get_model_definition(model_id),
            'data': request.db.get_data(model_id)}


@model.put(validators=(model_validator,), permission='put_model')
def put_model(request):
    model_id = request.matchdict['model_id']

    # DELETE ALL THE THINGS.
    request.db.delete_model(model_id)

    request.db.put_model(request.validated['definition'], users, policy_id, model_id)

    for data_item in request.validated['data']:
        request.db.put_data_item(model_id, data_item)

    return "ok"
