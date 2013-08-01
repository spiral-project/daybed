from cornice import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect

from daybed.validators import definition_validator


definition = Service(name='model-definition',
                     path='/models/{model_id}/definition',
                     description='Model Definitions',
                     renderer="jsonp",
                     cors_origins=('*',))


@definition.get()
def get_definition(request):
    """Retrieves a model definition"""
    model_id = request.matchdict['model_id']
    doc = request.db.get_model_definition(model_id)
    if doc:
        return doc['definition']
    raise HTTPNotFound(detail="Unknown model %s" % model_id)


@definition.put(validators=(definition_validator,))
def put_definition(request):
    """Create or update a model definition.

    Checks that the data is a valid model definition.

    """
    model_id = request.matchdict['model_id']
    request.db.put_model_definition(request.data_clean, model_id)
    return "ok"


@definition.delete()
def delete_definition(request):
    raise HTTPTemporaryRedirect(request.url.replace('/definition', ''))
