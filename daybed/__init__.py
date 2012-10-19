"""Main entry point
"""
import logging
from couchdb.client import Server
from couchdb.http import PreconditionFailed

from pyramid.config import Configurator
from pyramid.events import NewRequest
from daybed.db import DatabaseConnection, sync_couchdb_views

logger = logging.getLogger('daybed')

def add_db_to_request(event):
    request = event.request
    settings = request.registry.settings
    con_info = settings['db_server'][settings['db_name']]
    event.request.db = DatabaseConnection(con_info)


def create_db_if_not_exist(server, db_name):
    try:
        server.create(db_name)
        logger.info('CouchDB database "%s" successfully created.' % db_name)
    except PreconditionFailed:
        logger.info('CouchDB database "%s" already exists.' % db_name)
        pass

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("daybed.views")

    # CouchDB initialization
    db_server = Server(settings['couchdb_uri'])
    config.registry.settings['db_server'] = db_server
    create_db_if_not_exist(db_server, settings['db_name'])
    sync_couchdb_views(db_server[settings['db_name']])
    config.add_subscriber(add_db_to_request, NewRequest)
    return config.make_wsgi_app()
