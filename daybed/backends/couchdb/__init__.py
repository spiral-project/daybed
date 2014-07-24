import os
import socket

from couchdb.client import Server
from couchdb.http import PreconditionFailed
from couchdb.design import ViewDefinition

from daybed import logger
from .views import docs

from . import views
from daybed.backends.exceptions import (
    TokenAlreadyExist, TokenNotFound, ModelNotFound, RecordNotFound
)


class CouchDBBackendConnectionError(Exception):
    pass


class CouchDBBackend(object):

    @classmethod
    def load_from_config(cls, config):
        settings = config.registry.settings

        generator = config.maybe_dotted(settings['daybed.id_generator'])
        return CouchDBBackend(
            host=settings['backend.db_host'],
            db_name=os.environ.get('DB_NAME', settings['backend.db_name']),
            id_generator=generator(config)
        )

    def __init__(self, host, db_name, id_generator):
        self.server = Server(host)
        self.db_name = db_name

        try:
            self.create_db_if_not_exist()
        except socket.error as e:
            raise CouchDBBackendConnectionError(
                "Unable to connect to the CouchDB server: %s - %s" % (host, e))

        self._db = self.server[self.db_name]
        self.sync_views()
        self._generate_id = id_generator

    def delete_db(self):
        del self.server[self.db_name]

    def create_db_if_not_exist(self):
        try:
            self.server.create(self.db_name)
            logger.info('Creating and using db "%s"' % self.db_name)
        except PreconditionFailed:
            logger.info('Using db "%s".' % self.db_name)

    def sync_views(self):
        ViewDefinition.sync_many(self.server[self.db_name], docs)

    def __get_raw_model(self, model_id):
        try:
            doc = views.model_definitions(self._db)[model_id].rows[0]
            return doc.value
        except IndexError:
            raise ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_raw_model(model_id)['definition']

    def __get_raw_records(self, model_id):
        return views.records(self._db)[model_id]

    def get_records(self, model_id):
        records = []
        for item in self.__get_raw_records(model_id):
            item.value['record']['id'] = item.value['_id'].split('-')[1]
            records.append(item.value['record'])
        return records

    def __get_raw_record(self, model_id, record_id):
        key = u'-'.join((model_id, record_id))
        try:
            return views.records_all(self._db)[key].rows[0].value
        except IndexError:
            raise RecordNotFound(u'(%s, %s)' % (model_id, record_id))

    def get_record(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        return doc['record']

    def get_record_authors(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        return doc['authors']

    def put_model(self, definition, acls, model_id=None):
        if model_id is None:
            model_id = self._generate_id()

        definition_id, _ = self._db.save({
            'type': 'definition',
            '_id': model_id,
            'definition': definition,
            'acls': acls})
        return definition_id

    def put_record(self, model_id, record, authors, record_id=None):
        doc = {
            'type': 'record',
            'authors': authors,
            'model_id': model_id,
            'record': record}

        if record_id is not None:
            try:
                old_doc = self.__get_raw_record(model_id, record_id)
            except RecordNotFound:
                doc['_id'] = '-'.join((model_id, record_id))
            else:
                authors = list(set(authors) | set(old_doc['authors']))
                doc['authors'] = authors
                old_doc.update(doc)
                doc = old_doc
        else:
            record_id = self._generate_id()
            doc['_id'] = '-'.join((model_id, record_id))

        self._db.save(doc)
        return record_id

    def delete_record(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        if doc:
            self._db.delete(doc)
        return doc

    def delete_records(self, model_id):
        results = self.__get_raw_records(model_id)
        for result in results:
            self._db.delete(result.value)
        return results

    def delete_model(self, model_id):
        """DELETE ALL THE THINGS"""

        # Delete the associated data if any.
        self.delete_records(model_id)

        try:
            doc = views.model_definitions(self._db)[model_id].rows[0].value
        except IndexError:
            raise ModelNotFound(model_id)

        # Delete the model definition if it exists.
        self._db.delete(doc)
        return doc

    def __get_raw_token(self, tokenHmacId):
        try:
            return views.tokens(self._db)[tokenHmacId].rows[0].value
        except IndexError:
            raise TokenNotFound(tokenHmacId)

    def get_token(self, tokenHmacId):
        """Returns the information associated with an token"""
        token = dict(**self.__get_raw_token(tokenHmacId))
        return token['secret']

    def add_token(self, tokenHmacId, secret):
        # Check that the token doesn't already exist.
        try:
            self.__get_raw_token(tokenHmacId)
            raise TokenAlreadyExist(tokenHmacId)
        except TokenNotFound:
            pass

        doc = dict(secret=secret, name=tokenHmacId, type='token')
        self._db.save(doc)

    def get_model_acls(self, model_id):
        doc = self.__get_raw_model(model_id)
        return doc['acls']
