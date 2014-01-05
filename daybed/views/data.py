import json

from cornice import Service

from daybed.backends.exceptions import RecordNotFound
from daybed.schemas.validators import (RecordValidator, record_validator,
                                       validate_against_schema)
from daybed.acl import USER_EVERYONE


data = Service(name='data',
               path='/models/{model_id}/data',
               description='Model data',
               renderer='jsonp')


record = Service(name='record',
                 path='/models/{model_id}/data/{record_id}',
                 description='Model',
                 renderer="jsonp")


@data.get(permission='get_data')
@data.get(accept='application/geojson', renderer='geojson',
          permission='get_data')
def get_data(request):
    """Retrieves all model records."""
    model_id = request.matchdict['model_id']
    # Check that model is defined
    exists = request.db.get_model_definition(model_id)
    if not exists:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}
    # Return array of records
    results = request.db.get_records(model_id)
    return {'data': results}


@data.post(validators=record_validator, permission='post_data')
def post_data(request):
    """Saves a model data.

    Posted data fields will be matched against their related model
    definition.

    """
    # if we are asked only for validation, don't do anything more.
    if request.headers.get('X-Daybed-Validate-Only', 'false') == 'true':
        return

    model_id = request.matchdict['model_id']
    if request.user:
        username = request.user['name']
    else:
        username = USER_EVERYONE
    data_id = request.db.put_record(model_id, request.data_clean,
                                    username)
    created = u'%s/models/%s/data/%s' % (request.application_url, model_id,
                                         data_id)
    request.response.status = "201 Created"
    request.response.headers['location'] = str(created)
    return {'id': data_id}


@data.delete(permission='delete_data')
def delete_data(request):
    model_id = request.matchdict['model_id']
    request.db.delete_records(model_id)
    return {"msg": "ok"}


@record.get(permission='get_record')
def get(request):
    """Retrieves all model records."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']
    try:
        return request.db.get_record(model_id, record_id)
    except RecordNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: record not found %s" % (model_id, record_id)}


@record.put(validators=record_validator, permission='put_record')
def put(request):
    """Update or create a record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']

    if request.user:
        username = request.user['name']
    else:
        username = USER_EVERYONE

    data_id = request.db.put_record(model_id, request.data_clean,
                                    [username], record_id=record_id)
    return {'id': data_id}


@record.patch(permission='patch_record')
def patch(request):
    """Update or create a record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']

    if request.user:
        username = request.user['name']
    else:
        username = USER_EVERYONE

    try:
        data = request.db.get_record(model_id, record_id)
    except RecordNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: record not found %s" % (model_id, record_id)}

    data.update(json.loads(request.body.decode('utf-8')))
    definition = request.db.get_model_definition(model_id)
    validate_against_schema(request, RecordValidator(definition), data)
    if not request.errors:
        request.db.put_record(model_id, data, [username], record_id)
    return {'id': record_id}


@record.delete(permission='delete_record')
def delete(request):
    """Delete the record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']

    deleted = request.db.delete_record(model_id, record_id)
    if not deleted:
        request.response.status = "404 Not Found"
        return {"msg": "%s: record not found %s" % (model_id, record_id)}
    return {"msg": "ok"}
