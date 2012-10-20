from cornice import Service
from cornice.spore import generate_spore

from daybed import VERSION

spore = Service(name="spore",
                path='/spore',
                description="Spore endpoint",
                renderer="jsonp")

@spore.get()
def get_spore(request):
    return generate_spore(get_services(), 'daybed', request.application_url, VERSION)
