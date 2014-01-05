import json
from cornice import Service

from daybed.backends.exceptions import DataItemNotFound
from daybed.validators import schema_validator, validate_against_schema
from daybed.schemas import SchemaValidator


data = Service(name='data',
               path='/models/{model_id}/data',
               description='Model data',
               renderer='jsonp')


data_item = Service(name='data_item',
                    path='/models/{model_id}/data/{data_item_id}',
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
    results = request.db.get_data_items(model_id)
    return {'data': results}


@data.post(validators=schema_validator, permission='post_data')
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
        username = 'system.Everyone'
    data_id = request.db.put_data_item(model_id, request.data_clean,
                                       username)
    created = u'%s/models/%s/data/%s' % (request.application_url, model_id,
                                         data_id)
    request.response.status = "201 Created"
    request.response.headers['location'] = str(created)
    return {'id': data_id}


@data.delete(permission='delete_data')
def delete_data(request):
    model_id = request.matchdict['model_id']
    request.db.delete_data_items(model_id)
    return {"msg": "ok"}


@data_item.get(permission='get_data_item')
def get(request):
    """Retrieves all model records."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']
    try:
        return request.db.get_data_item(model_id, data_item_id)
    except DataItemNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: data_item not found %s" % (model_id, data_item_id)}


@data_item.put(validators=schema_validator, permission='put_data_item')
def put(request):
    """Update or create a data item."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']

    if request.user:
        username = request.user['name']
    else:
        username = 'system.Everyone'

    data_id = request.db.put_data_item(model_id, request.data_clean,
                                       [username],
                                       data_item_id=data_item_id)
    return {'id': data_id}


@data_item.patch(permission='patch_data_item')
def patch(request):
    """Update or create a data item."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']

    if request.user:
        username = request.user['name']
    else:
        username = 'system.Everyone'

    try:
        data = request.db.get_data_item(model_id, data_item_id)
    except DataItemNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: data_item not found %s" % (model_id, data_item_id)}

    data.update(json.loads(request.body.decode('utf-8')))
    definition = request.db.get_model_definition(model_id)
    validate_against_schema(request, SchemaValidator(definition), data)
    if not request.errors:
        request.db.put_data_item(model_id, data, [username],
                                 data_item_id)
    return {'id': data_item_id}


@data_item.delete(permission='delete_data_item')
def delete(request):
    """Delete the data item."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']

    deleted = request.db.delete_data_item(model_id, data_item_id)
    if not deleted:
        request.response.status = "404 Not Found"
        return {"msg": "%s: data_item not found %s" % (model_id, data_item_id)}
    return {"msg": "ok"}
