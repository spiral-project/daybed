from cornice import Service
from daybed.schemas import registry


fields = Service(name='fields',
                 path='/fields',
                 description='The resource containing all the fields',
                 renderer='jsonp')


@fields.get()
def list_fields(request):
    return registry.names
