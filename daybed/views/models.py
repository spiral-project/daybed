from cornice import Service
from pyramid.security import Everyone

from daybed.permissions import (
    invert_permissions_matrix, merge_permissions, default_model_permissions
)
from daybed.backends.exceptions import ModelNotFound
from daybed.views.errors import forbidden_view
from daybed.schemas.validators import model_validator, permissions_validator


models = Service(name='models', path='/models', description='Models')


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


permissions = Service(name='model-permissions',
                      path='/models/{model_id}/permissions',
                      description='Model permissions',
                      renderer="jsonp",
                      cors_origins=('*',))


@definition.get(permission='get_definition')
def get_definition(request):
    """Retrieves a model definition."""
    model_id = request.matchdict['model_id']
    try:
        return request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.errors.add('path', model_id, "model not found")
        request.errors.status = "404 Not Found"


@permissions.get(permission='get_permissions')
def get_permissions(request):
    """Retrieves a model permissions."""
    model_id = request.matchdict['model_id']
    try:
        permissions = request.db.get_model_permissions(model_id)
        return invert_permissions_matrix(permissions)
    except ModelNotFound:
        request.errors.add('path', model_id, "model not found")
        request.errors.status = "404 Not Found"


@permissions.patch(permission='put_permissions',
                   validators=(permissions_validator,))
def patch_permissions(request):
    """Update a model permissions."""
    model_id = request.matchdict['model_id']
    definition = request.db.get_model_definition(model_id)

    current_permissions = request.db.get_model_permissions(model_id)
    permissions = merge_permissions(current_permissions, request.data_clean)

    request.db.put_model(definition, permissions, model_id)
    return invert_permissions_matrix(permissions)


@permissions.put(permission='put_permissions',
                 validators=(permissions_validator,))
def put_permissions(request):
    """Update a model permissions."""
    model_id = request.matchdict['model_id']
    definition = request.db.get_model_definition(model_id)

    permissions = merge_permissions({}, request.data_clean)

    request.db.put_model(definition, permissions, model_id)
    return invert_permissions_matrix(permissions)


@models.get(permission='get_models')
def get_models(request):
    """Return the list of modelname readable by the user."""
    return {"models": request.db.get_models(request.principals)}


@models.post(permission='post_model', validators=(model_validator,))
def post_models(request):
    """Creates a model with the given definition and records, if any."""
    if request.credentials_id:
        credentials_id = request.credentials_id
    else:
        credentials_id = Everyone

    specified_perms = request.data_clean['permissions']
    default_perms = default_model_permissions(credentials_id)
    permissions = merge_permissions(default_perms, specified_perms)

    model_id = request.db.put_model(
        definition=request.data_clean['definition'],
        permissions=permissions)

    request.notify('ModelCreated', model_id)

    for record in request.data_clean['records']:
        record_id = request.db.put_record(model_id, record, [credentials_id])
        request.notify('RecordCreated', model_id, record_id)

    request.response.status = "201 Created"
    location = '%s/models/%s' % (request.application_url, model_id)
    request.response.headers['location'] = str(location)
    return {'id': model_id}


@model.delete(permission='delete_model')
def delete_model(request):
    """Deletes a model and its records."""
    model_id = request.matchdict['model_id']
    try:
        model = request.db.delete_model(model_id)
    except ModelNotFound:
        request.errors.status = "404 Not Found"
        request.errors.add('path', model_id, "model not found")
        return

    request.notify('ModelDeleted', model_id)

    model["permissions"] = invert_permissions_matrix(model["permissions"])
    return model


@model.get(permission='get_model')
def get_model(request):
    """Retrieves the full model, definition and records."""
    model_id = request.matchdict['model_id']
    try:
        definition = request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.errors.add('path', model_id, "model not found")
        request.errors.status = "404 Not Found"
        return

    if "read_all_records" not in request.permissions:
        records = request.db.get_records_with_authors(model_id)
        records = [r["record"] for r in records
                   if set(request.principals).intersection(r["authors"])]
    else:
        records = request.db.get_records(model_id)

    permissions = request.db.get_model_permissions(model_id)
    return {'definition': definition,
            'records': records,
            'permissions': invert_permissions_matrix(permissions)}


@model.put(validators=(model_validator,), permission='post_model')
def put_model(request):
    model_id = request.matchdict['model_id']

    try:
        request.db.get_model(model_id)

        if request.has_permission('put_model'):
            try:
                request.db.delete_model(model_id)
            except ModelNotFound:
                pass
            return handle_put_model(request)
    except ModelNotFound:
        return handle_put_model(request, create=True)

    return forbidden_view(request)


def handle_put_model(request, create=False):
    model_id = request.matchdict['model_id']

    if request.credentials_id:
        credentials_id = request.credentials_id
    else:
        credentials_id = Everyone

    specified_perms = request.data_clean['permissions']
    default_perms = default_model_permissions(credentials_id)
    permissions = merge_permissions(default_perms, specified_perms)

    request.db.put_model(request.data_clean['definition'],
                         permissions,
                         model_id)

    event = 'ModelCreated' if create else 'ModelUpdated'
    request.notify(event, model_id)

    for record in request.data_clean['records']:
        record_id = request.db.put_record(model_id, record, [credentials_id])
        request.notify('RecordCreated', model_id, record_id)

    return {"id": model_id}
