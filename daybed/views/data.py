import json

from cornice import Service
from pyramid.exceptions import NotFound

from daybed.validators import schema_validator

data = Service(name='data',
               path='/models/{model_id}/data',
               description='Model data',
               renderer='jsonp')


@data.get()
def get_data(request):
    """Retrieves all model records."""
    model_id = request.matchdict['model_id']
    # Check that model is defined
    exists = request.db.get_model_definition(model_id)
    if not exists:
        raise NotFound(detail="Unknown model %s" % model_id)
    # Return array of records
    results = request.db.get_data_items(model_id)
    data = []
    for result in results:
        result.value['data']['id'] = result._id
        data.append(result.value['data'])
    return {'data': data}


@data.post(validators=schema_validator)
def post_data(request):
    """Saves a model record.

    Posted data fields will be matched against their related model
    definition.

    """
    # if we are asked only for validation, don't do anything more.
    if request.headers.get('X-Daybed-Validate-Only', 'false') == 'true':
        return

    model_id = request.matchdict['model_id']
    data_id = request.db.put_data_item(model_id, json.loads(request.body))
    created = '%s/models/%s/data/%s' % (request.application_url, model_id,
                                        data_id)
    request.response.status = "201 Created"
    request.response.headers['location'] = created
    return {'id': data_id}


@data.delete()
def delete_data(request):
    model_id = request.matchdict['model_id']
    request.db.delete_data_items(model_id)
