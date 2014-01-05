import json

from cornice import Service

from daybed.validators import validate_against_schema
from daybed.schemas import DefinitionValidator, SchemaValidator, RolesValidator
from daybed.backends.exceptions import ModelNotFound, PolicyNotFound


models = Service(name='models', path='/models', description='Models',
                 renderer="jsonp", cors_origins=('*',))


model = Service(name='model',
                path='/models/{model_id}',
                description='Model',
                renderer="jsonp",
                cors_origins=('*',))


definition = Service(name='model-definition',
                     path='/models/{model_id}/definition',
                     description='Model Definitions',
                     renderer="jsonp",
                     cors_origins=('*',))


def model_validator(request):
    """Verify that the model is okay (that we have the right fields) and
    eventually populates it if there is a need to.
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
    except ValueError:
        request.errors.add('body', 'json value error', "body malformed")
        return

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

    # Check that roles are valid.
    if request.user:
        default_roles = {'admins': [request.user['name']]}
    else:
        default_roles = {'admins': ["system.Everyone"]}
    roles = body.get('roles', default_roles)
    validate_against_schema(request, RolesValidator(), roles)

    request.validated['roles'] = roles
    policy_id = body.get('policy_id', request.registry.default_policy)

    # Check that the policy exists in our db.
    try:
        request.db.get_policy(policy_id)
    except PolicyNotFound:
        request.errors.add('body', 'policy_id',
                           "policy '%s' doesn't exist" % policy_id)
    request.validated['policy_id'] = policy_id


@definition.get(permission='get_definition')
def get_definition(request):
    """Retrieves a model definition"""
    model_id = request.matchdict['model_id']
    try:
        return request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}


@models.post(permission='post_model', validators=(model_validator,))
def post_models(request):
    """creates a model with the given definition and data, if any."""
    model_id = request.db.put_model(
        definition=request.validated['definition'],
        roles=request.validated['roles'],
        policy_id=request.validated['policy_id'])

    if request.user:
        username = request.user['name']
    else:
        username = 'system.Everyone'

    for data_item in request.validated['data']:
        request.db.put_data_item(model_id, data_item, [username])

    request.response.status = "201 Created"
    location = '%s/models/%s' % (request.application_url, model_id)
    request.response.headers['location'] = str(location)
    return {'id': model_id}


@model.delete(permission='delete_model')
def delete_model(request):
    """Deletes a model and its matching associated data."""
    model_id = request.matchdict['model_id']
    try:
        request.db.delete_model(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}
    return {"msg": "ok"}


@model.get(permission='get_model')
def get_model(request):
    """Returns the full model definition."""
    model_id = request.matchdict['model_id']

    try:
        definition = request.db.get_model_definition(model_id),
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}

    return {'definition': definition,
            'data': request.db.get_data_items(model_id),
            'policy_id': request.db.get_model_policy_id(model_id),
            'roles': request.db.get_roles(model_id)}


@model.put(validators=(model_validator,), permission='put_model')
def put_model(request):
    model_id = request.matchdict['model_id']

    # DELETE ALL THE THINGS.
    try:
        request.db.delete_model(model_id)
    except ModelNotFound:
        pass

    if request.user:
        username = request.user['name']
    else:
        username = 'system.Everyone'

    request.db.put_model(request.validated['definition'],
                         request.validated['roles'],
                         request.validated['policy_id'],
                         model_id)

    for data_item in request.validated['data']:
        request.db.put_data_item(model_id, data_item, [username])

    return {"id": model_id}
