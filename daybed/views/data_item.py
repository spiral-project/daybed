from cornice import Service
from pyramid.exceptions import NotFound

from daybed.validators import schema_validator, token_validator


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

    return result.value


@data_item.put(validators=schema_validator)
def put(request):
    """Update a data item.

    Checks that the data is a valid data item.

    """
    model_name = request.matchdict['model_name']
    data_item_id = request.matchdict['data_item_id']

    data_doc = {
        '_id': data_item_id,
        'type': 'data',
        'model_name': model_name,
        'data': json.loads(request.body)
    }
    _id, rev = request.db.save(data_doc)
    return {'id': _id}


@data_item.delete(validators=schema_validator)
def delete(request):
    """Delete the data item.

    Checks that the data is a valid data item.

    """
    model_name = request.matchdict['model_name']
    data_item_id = request.matchdict['data_item_id']

    result = request.db.get_data_item(data_item_id)
    request.db.delete(result)
