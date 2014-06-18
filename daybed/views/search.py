from cornice import Service

from daybed.backends.exceptions import ModelNotFound


search = Service(name='search',
                 path='/models/{model_id}/search/',
                 description='Search records',
                 renderer='jsonp')


@search.get(permission='get_records')
def search_records(request):
    """Search model records."""
    model_id = request.matchdict['model_id']
    try:
        request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {"msg": "%s: model not found" % model_id}

    results = request.index.search(index=model_id,
                                   doc_type=model_id,
                                   body=request.body)
    return results
