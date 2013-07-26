import json

from cornice import Service
from pyramid.exceptions import NotFound

from daybed.validators import schema_validator, validate_against_schema
from daybed.schemas import SchemaValidator


data_item = Service(name='data_item',
                    path='/models/{model_id}/data/{data_item_id}',
                    description='Model',
                    renderer="jsonp")


@data_item.get()
def get(request):
    """Retrieves all model records."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']

    # Check that model is defined
    result = request.db.get_data_item(model_id, data_item_id)
    if not result:
        raise NotFound("Unknown data_item %s: %s" % (model_id, data_item_id))

    return result['data']


@data_item.put(validators=schema_validator)
def put(request):
    """Update or create a data item."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']
    data_id = request.db.put_data_item(model_id, json.loads(request.body),
                                       data_item_id)
    return {'id': data_id}


@data_item.patch()
def patch(request):
    """Update or create a data item."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']
    data_item = request.db.get_data_item(model_id, data_item_id)
    if not data_item:
        raise NotFound(
            "Unknown data_item %s: %s" % (model_id, data_item_id)
        )
    data = data_item['data']
    data.update(json.loads(request.body))
    definition = request.db.get_model_definition(model_id)['definition']
    validate_against_schema(request, SchemaValidator(request, definition), data)
    if not request.errors:
        request.db.put_data_item(model_id, data, data_item_id)
    return {'id': data_item_id}


@data_item.delete()
def delete(request):
    """Delete the data item."""
    model_id = request.matchdict['model_id']
    data_item_id = request.matchdict['data_item_id']

    deleted = request.db.delete_data_item(model_id, data_item_id)
    if not deleted:
        raise NotFound("Unknown data_item %s: %s" % (model_id, data_item_id))
