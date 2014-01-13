from cornice import Service

from daybed.backends.exceptions import ModelNotFound
from daybed.schemas.validators import model_validator


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


@definition.get(permission='get_definition')
def get_definition(request):
    """Retrieves a model definition."""
    model_id = request.matchdict['model_id']
    try:
        return request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}


@models.post(permission='post_model', validators=(model_validator,))
def post_models(request):
    """Creates a model with the given definition and records, if any."""
    model_id = request.db.put_model(
        definition=request.validated['definition'],
        roles=request.validated['roles'],
        policy_id=request.validated['policy_id'])

    if request.user:
        username = request.user['name']
    else:
        username = 'system.Everyone'

    for record in request.validated['records']:
        request.db.put_record(model_id, record, [username])

    request.response.status = "201 Created"
    location = '%s/models/%s' % (request.application_url, model_id)
    request.response.headers['location'] = str(location)
    return {'id': model_id}


@model.delete(permission='delete_model')
def delete_model(request):
    """Deletes a model and its records."""
    model_id = request.matchdict['model_id']
    try:
        request.db.delete_model(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}
    return {"msg": "ok"}


@model.get(permission='get_model')
def get_model(request):
    """Retrieves the full model, definition and records."""
    model_id = request.matchdict['model_id']
    try:
        definition = request.db.get_model_definition(model_id),
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}

    return {'definition': definition,
            'records': request.db.get_records(model_id),
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

    for record in request.validated['records']:
        request.db.put_record(model_id, record, [username])

    return {"id": model_id}
