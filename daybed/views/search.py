import six
from cornice import Service

from daybed import logger
from daybed.backends.exceptions import ModelNotFound


search = Service(name='search',
                 path='/models/{model_id}/search/',
                 description='Search records',
                 renderer='jsonp')


@search.get(permission='get_all_records')
def search_records(request):
    """Search model records."""
    model_id = request.matchdict['model_id']
    try:
        request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}

    # So far we just support query from body
    query = request.body

    # In case request body arrives as bytes under python 3
    if isinstance(query, six.binary_type):
        query = query.decode('utf-8')

    try:
        results = request.index.search(model_id, query)
        return results
    except Exception as e:
        logger.error(e)
        request.response.status = "502 Bad Gateway"
        return {"msg": "Could not obtain response from indexing service"}
