from six import iteritems
from collections import defaultdict
from cornice import Service
from pyramid.security import Everyone

from daybed.acl import (
    get_model_acls, invert_acls_matrix, dict_list2set, dict_set2list,
    PERMISSIONS_SET
)
from daybed.backends.exceptions import ModelNotFound
from daybed.views.errors import forbidden_view
from daybed.schemas.validators import model_validator, acls_validator


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


acls = Service(name='model-acls',
               path='/models/{model_id}/acls',
               description='Model ACLs',
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


@acls.get(permission='get_acls')
def get_acls(request):
    """Retrieves a model acls."""
    model_id = request.matchdict['model_id']
    try:
        return invert_acls_matrix(request.db.get_model_acls(model_id))
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}


@acls.patch(permission='put_acls', validators=(acls_validator,))
def patch_acls(request):
    """Update a model acls."""
    model_id = request.matchdict['model_id']
    definition = request.db.get_model_definition(model_id)
    acls = dict_list2set(request.db.get_model_acls(model_id))

    for token, perms in iteritems(request.validated['acls']):
        # Handle remove all
        if '-all' in [perm.lower() for perm in perms]:
            for p in PERMISSIONS_SET:
                acls[p].discard(token)
        # Handle add all
        elif 'all' in [perm.lstrip('+').lower() for perm in perms]:
            for p in PERMISSIONS_SET:
                acls[p].add(token)
        # Handle add/remove perms list
        else:
            for perm in perms:
                perm = perm.lower()
                if perm.startswith('-'):
                    acls[perm.lstrip('-')].discard(token)
                else:
                    acls[perm.lstrip('+')].add(token)

    request.db.put_model(definition, dict_set2list(acls), model_id)
    return invert_acls_matrix(acls)


@acls.put(permission='put_acls', validators=(acls_validator,))
def put_acls(request):
    """Update a model acls."""
    model_id = request.matchdict['model_id']
    definition = request.db.get_model_definition(model_id)
    acls = defaultdict(set)
    for token, perms in iteritems(request.validated['acls']):
        for perm in perms:
            if not perm.startswith('-'):
                acls[perm.lstrip('+')].add(token)
    request.db.put_model(definition, dict_set2list(acls))
    return invert_acls_matrix(acls)


@models.post(permission='post_model', validators=(model_validator,))
def post_models(request):
    """Creates a model with the given definition and records, if any."""
    if request.token:
        token = request.token
    else:
        token = Everyone

    model_id = request.db.put_model(
        definition=request.validated['definition'],
        acls=get_model_acls(token))

    for record in request.validated['records']:
        request.db.put_record(model_id, record, [token])

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
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}
    return model


@model.get(permission='get_model')
def get_model(request):
    """Retrieves the full model, definition and records."""
    model_id = request.matchdict['model_id']
    try:
        definition = request.db.get_model_definition(model_id),
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}

    records = request.db.get_records(model_id)

    if "read_all_records" not in request.permissions:
        records = [r for r in records
                   if set(request.principals).intersection(r.authors)]

    return {'definition': definition,
            'records': records,
            'acls': invert_acls_matrix(request.db.get_model_acls(model_id))}


@model.put(validators=(model_validator,), permission='post_model')
def put_model(request):
    model_id = request.matchdict['model_id']

    try:
        request.db.get_model_definition(model_id)

        if request.has_permission('put_model'):
            try:
                request.db.delete_model(model_id)
            except ModelNotFound:
                pass
            return handle_put_model(request)
    except ModelNotFound:
        return handle_put_model(request)

    return forbidden_view(request)


def handle_put_model(request):
    model_id = request.matchdict['model_id']

    if request.token:
        token = request.token
    else:
        token = Everyone

    request.db.put_model(request.validated['definition'],
                         get_model_acls(token),
                         model_id)

    for record in request.validated['records']:
        request.db.put_record(model_id, record, [token])

    return {"id": model_id}
