"""Main entry point
"""
import couchdb

from pyramid.config import Configurator
from pyramid.events import NewRequest
from couchdb.design import ViewDefinition

from views import __design_docs__


def add_couchdb_to_request(event):
    request = event.request
    settings = request.registry.settings
    db = settings['db_server'][settings['db_name']]
    event.request.db = db


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("daybed.views")
    # CouchDB initialization
    db_server = couchdb.client.Server(settings['couchdb_uri'])
    config.registry.settings['db_server'] = db_server
    ViewDefinition.sync_many(db_server[settings['db_name']], __design_docs__)
    config.add_subscriber(add_couchdb_to_request, NewRequest)
    return config.make_wsgi_app()
