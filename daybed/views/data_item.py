from cornice import Service
from pyramid.exceptions import NotFound


data_item = Service(name='data_item',
                    path='/data/{model_name}/{data_item_id}',
                    description='Model',
                    renderer="jsonp")


@data_item.get()
def get_data(request):
    """Retrieves all model records."""
    model_name = request.matchdict['model_name']
    data_item_id = request.matchdict['data_item_id']

    # Check that model is defined
    result = request.db.get_data_item(model_name, data_item_id)
    if not result:
        raise NotFound("Unknown data_item %s: %s" % (model_name, data_item_id))

    return result.value
