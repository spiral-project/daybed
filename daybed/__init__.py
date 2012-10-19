"""Main entry point
"""
import couchdb

from pyramid.config import Configurator
from pyramid.events import NewRequest
from daybed.db import DatabaseConnection, sync_couchdb_views


def add_db_to_request(event):
    request = event.request
    settings = request.registry.settings
    con_info = settings['db_server'][settings['db_name']]
    event.request.db = DatabaseConnection(con_info)


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("daybed.views")

    # CouchDB initialization
    db_server = couchdb.client.Server(settings['couchdb_uri'])
    config.registry.settings['db_server'] = db_server
    sync_couchdb_views(db_server[settings['db_name']])

    config.add_subscriber(add_db_to_request, NewRequest)
    return config.make_wsgi_app()
