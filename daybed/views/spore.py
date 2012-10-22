from cornice import Service
from cornice.ext.spore import generate_spore_description
from cornice.service import get_services

from daybed import VERSION

spore = Service(name="spore",
                path='/spore',
                description="Spore endpoint",
                renderer="jsonp")


@spore.get()
def get_spore(request):
    return generate_spore_description(get_services(), 'daybed',
              request.application_url, VERSION)
