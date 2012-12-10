import json

from cornice import Service
from pyramid.exceptions import NotFound

from daybed.validators import schema_validator


data_item = Service(name='data_item',
                    path='/data/{model_name}/{data_item_id}',
                    description='Model',
                    renderer="jsonp")


@data_item.get()
def get(request):
    """Retrieves all model records."""
    model_name = request.matchdict['model_name']
    data_item_id = request.matchdict['data_item_id']

    # Check that model is defined
    result = request.db.get_data_item(model_name, data_item_id)
    if not result:
        raise NotFound("Unknown data_item %s: %s" % (model_name, data_item_id))

    return result.value['data']


@data_item.put(validators=schema_validator)
def put(request):
    """Update or create a data item."""
    model_name = request.matchdict['model_name']
    data_item_id = request.matchdict['data_item_id']
    data_id = request.db.create_data(model_name, json.loads(request.body),
                                     data_item_id)
    return {'id': data_id}


@data_item.delete()
def delete(request):
    """Delete the data item."""
    model_name = request.matchdict['model_name']
    data_item_id = request.matchdict['data_item_id']

    result = request.db.get_data_item(model_name, data_item_id)
    if result:
        request.db.db.delete(result.value)
    else:
        raise NotFound("Unknown data_item %s: %s" % (model_name, data_item_id))
