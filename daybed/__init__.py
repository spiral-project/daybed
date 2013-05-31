"""Main entry point
"""
VERSION = '0.1'

from cornice import Service
from pyramid.config import Configurator
from pyramid.renderers import JSONP

from daybed.renderers import GeoJSON


def main(global_config, **settings):
    Service.cors_origins = ('*',)

    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("daybed.views")

    # backend initialisation
    backend = config.maybe_dotted(settings['daybed.backend'])
    config.registry.backend = backend(config)

    config.add_renderer('jsonp', JSONP(param_name='callback'))
    config.add_renderer('geojson', GeoJSON())
    return config.make_wsgi_app()
