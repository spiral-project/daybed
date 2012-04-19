"""Main entry point
"""
from pyramid.config import Configurator


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    #config.include("couchdb")
    config.scan("daybed.views")
    return config.make_wsgi_app()
