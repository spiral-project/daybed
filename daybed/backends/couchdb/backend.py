import os
import logging

from pyramid.events import NewRequest

from couchdb.client import Server
from couchdb.http import PreconditionFailed
from couchdb.design import ViewDefinition

from .designdocs import docs
from .database import Database


logger = logging.getLogger(__name__)


class CouchDBBackend(object):
    @property
    def db(self):
        return self.server[self.db_name]

    def __init__(self, config):
        settings = config.registry.settings

        self.config = config
        self.server = Server(settings['backend.db_host'])
        self.db_name = os.environ.get('DB_NAME', settings['backend.db_name'])

        self.create_db_if_not_exist()
        self.sync_views()
        self.config.add_subscriber(self.add_db_to_request, NewRequest)

    def delete_db(self):
        del self.server[self.db_name]

    def create_db_if_not_exist(self):
        try:
            self.server.create(self.db_name)
            logger.debug('Creating and using db "%s"' % self.db_name)
        except PreconditionFailed:
            logger.debug('Using db "%s".' % self.db_name)

    def sync_views(self):
        ViewDefinition.sync_many(self.db, docs)

    def add_db_to_request(self, event):
        event.request.db = Database(self.db)
