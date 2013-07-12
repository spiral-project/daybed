from cornice import Service
from pyramid.httpexceptions import HTTPTemporaryRedirect


models = Service(name='models',
                 path='/models/{model_id}',
                 description='Models',
                 renderer="jsonp",
                 cors_origins=('*',))


@models.delete()
def delete_model(request):
    """Deletes a model and its matching associated data."""
    model_id = request.matchdict['model_id']
    request.db.delete_model(model_id)
    return "ok"


@models.get()
def get_model(request):
    """Returns the definition and data of the given model"""
    model_id = request.matchdict['model_id']

    return {'definition': request.db.get_model_definition(model_id),
            'data': request.db.get_data(model_id)}


@models.put()
def put_model(request):
    # XXX Check that request.url is what we want (e.g. that's not changed by
    # a proxy or something similar
    raise HTTPTemporaryRedirect(request.url + '/definition')
