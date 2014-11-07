import os
import socket

import functools

from couchdb.client import Server
from couchdb.http import PreconditionFailed, Unauthorized
from couchdb.design import ViewDefinition

from daybed import logger
from .views import docs

from . import views
from daybed.backends import exceptions as backend_exceptions


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
        except (PreconditionFailed, Unauthorized):
            logger.info('Using db "%s".' % self.db_name)

    def sync_views(self):
        ViewDefinition.sync_many(self.server[self.db_name], docs)

    def get_models(self, principals):
        principals = list(set(principals))
        models = {}
        for result in views.models(self._db, keys=principals).rows:
            doc = result.value
            _id = doc["_id"]
            models[_id] = {
                "id": _id,
                "title": doc["definition"].get("title", _id),
                "description": doc["definition"].get("description", "")
            }
        return list(models.values())

    def __get_raw_model(self, model_id):
        try:
            doc = views.model_definitions(self._db, key=model_id).rows[0]
            return doc.value
        except IndexError:
            raise backend_exceptions.ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_raw_model(model_id)['definition']

    def __get_raw_records(self, model_id):
        # Make sure the model exists.
        self.__get_raw_model(model_id)
        return views.records(self._db, key=model_id).rows

    def get_records(self, model_id, raw_records=None):
        return [r["record"] for r in
                self.get_records_with_authors(model_id, raw_records)]

    def get_records_with_authors(self, model_id, raw_records=None):
        if raw_records is None:
            raw_records = self.__get_raw_records(model_id)
        records = []
        for item in raw_records:
            item.value['record']['id'] = item.value['_id'].split('-')[1]
            records.append({"authors": item.value['authors'],
                            "record": item.value['record']})
        return records

    def __get_raw_record(self, model_id, record_id):
        key = u'-'.join((model_id, record_id))
        try:
            return views.records_all(self._db, key=key).rows[0].value
        except IndexError:
            raise backend_exceptions.RecordNotFound(
                u'(%s, %s)' % (model_id, record_id)
            )

    def _model_exists(self, model_id):
        try:
            self.__get_raw_model(model_id)
            return True
        except backend_exceptions.ModelNotFound:
            return False

    def _record_exists(self, model_id, record_id):
        try:
            self.__get_raw_record(model_id, record_id)
            return True
        except backend_exceptions.RecordNotFound:
            return False

    def get_record(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        record = doc['record']
        record['id'] = record_id
        return record

    def get_record_authors(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        return doc['authors']

    def put_model(self, definition, permissions, model_id=None):
        if model_id is None:
            model_id = self._generate_id(key_exist=self._model_exists)

        try:
            doc = self.__get_raw_model(model_id)
        except backend_exceptions.ModelNotFound:
            doc = {'_id': model_id,
                   'type': 'definition'}
        doc['definition'] = definition
        doc['permissions'] = permissions

        definition_id, _ = self._db.save(doc)
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
            except backend_exceptions.RecordNotFound:
                doc['_id'] = '-'.join((model_id, record_id))
            else:
                authors = list(set(authors) | set(old_doc['authors']))
                doc['authors'] = authors
                old_doc.update(doc)
                doc = old_doc
        else:
            key_exist = functools.partial(self._record_exists, model_id)
            record_id = self._generate_id(key_exist=key_exist)
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
        return self.get_records(model_id, raw_records=results)

    def delete_model(self, model_id):
        """DELETE ALL THE THINGS"""

        # Delete the associated data if any.
        records = self.delete_records(model_id)

        try:
            doc = views.model_definitions(self._db, key=model_id).rows[0].value
        except IndexError:
            raise backend_exceptions.ModelNotFound(model_id)

        # Delete the model definition if it exists.
        self._db.delete(doc)
        return {"definition": doc["definition"],
                "permissions": doc["permissions"],
                "records": records}

    def __get_raw_token(self, credentials_id):
        try:
            return views.tokens(self._db, key=credentials_id).rows[0].value
        except IndexError:
            raise backend_exceptions.CredentialsNotFound(credentials_id)

    def get_token(self, credentials_id):
        """Returns the information associated with a credentials_id"""
        credentials = dict(**self.__get_raw_token(credentials_id))
        return credentials['token']

    def get_credentials_key(self, credentials_id):
        """Retrieves a token by its id"""
        credentials = dict(**self.__get_raw_token(credentials_id))
        return credentials['credentials']['key']

    def store_credentials(self, token, credentials):
        # Check that the token doesn't already exist.
        assert 'id' in credentials and 'key' in credentials
        try:
            self.__get_raw_token(credentials['id'])
            raise backend_exceptions.CredentialsAlreadyExist(credentials['id'])
        except backend_exceptions.CredentialsNotFound:
            pass

        doc = dict(token=token, credentials=credentials, type='token')
        self._db.save(doc)

    def get_model_permissions(self, model_id):
        doc = self.__get_raw_model(model_id)
        return doc['permissions']
