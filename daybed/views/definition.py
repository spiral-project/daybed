from cornice import Service
from pyramid.httpexceptions import HTTPNotFound


definition = Service(name='model-definition',
                 path='/models/{model_id}/definition',
                 description='Model Definitions',
                 renderer="jsonp",
                 cors_origins=('*',))


@definition.get(permission='get_definition')
def get_definition(request):
    """Retrieves a model definition"""
    model_id = request.matchdict['model_id']
    doc = request.db.get_model_definition(model_id)
    if doc:
        return doc['definition']
    raise HTTPNotFound(detail="Unknown model %s" % model_id)
