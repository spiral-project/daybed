import json

from cornice import Service
from pyramid.exceptions import NotFound

from daybed.validators import schema_validator

data = Service(name='data',
               path='/data/{model_name}',
               description='Model data',
               renderer='jsonp')


@data.get()
def get(request):
    """Retrieves all model records."""
    model_name = request.matchdict['model_name']
    # Check that model is defined
    exists = request.db.get_definition(model_name)
    if not exists:
        raise NotFound("Unknown model %s" % model_name)
    # Return array of records
    results = request.db.get_data(model_name)
    # TODO: Maybe we need to keep ids secret for editing
    data = []
    for result in results:
        result.value['data']['id'] = result.id
        data.append(result.value['data'])
    return {'data': data}


@data.post(validators=schema_validator)
def post(request):
    """Saves a model record.

    Posted data fields will be matched against their related model
    definition.

    """
    # if we are asked only for validation, don't do anything more.
    if request.headers.get('X-Daybed-Validate-Only', 'false') == 'true':
        return

    model_name = request.matchdict['model_name']
    data_id = request.db.create_data(model_name, json.loads(request.body))
    created = '%s/data/%s' % (request.application_url, data_id)
    request.response.status = "201 Created"
    request.response.headers['location'] = created
    return {'id': data_id}
