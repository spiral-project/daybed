from copy import deepcopy
import functools

from daybed.backends import exceptions as backend_exceptions


class MemoryBackend(object):

    @classmethod
    def load_from_config(cls, config):
        settings = config.registry.settings
        generator = config.maybe_dotted(settings['daybed.id_generator'])
        return MemoryBackend(generator(config))

    def __init__(self, id_generator):
        # model id generator
        self._generate_id = id_generator
        self._init_db()

    def delete_db(self):
        self._db.clear()
        self._init_db()

    def _init_db(self):
        self._db = {
            'models': {},
            'records': {},
            'permissions': {},
            'tokens': {},
            'credentials_keys': {}
        }

    def get_models(self, principals):
        principals = set(principals)
        models = self._db['models'].items()
        return [{"id": id,
                 "title": m["definition"].get("title", id),
                 "description": m["definition"].get("description", "")}
                for id, m in models if
                principals.intersection(m['permissions']['read_definition']) !=
                set()]

    def __get_raw_model(self, model_id):
        try:
            return deepcopy(self._db['models'][model_id])
        except KeyError:
            raise backend_exceptions.ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_raw_model(model_id)['definition']

    def __get_raw_records(self, model_id):
        try:
            return self._db['records'][model_id].values()
        except KeyError:
            raise backend_exceptions.ModelNotFound(model_id)

    def get_records(self, model_id, raw_records=None):
        return [r["record"] for r in
                self.get_records_with_authors(model_id, raw_records)]

    def get_records_with_authors(self, model_id, raw_records=None):
        if raw_records is None:
            raw_records = self.__get_raw_records(model_id)
        records = []
        for item in raw_records:
            item['record']['id'] = item['_id']
            records.append({"authors": deepcopy(item['authors']),
                            "record": deepcopy(item['record'])})
        return records

    def __get_raw_record(self, model_id, record_id):
        try:
            return deepcopy(self._db['records'][model_id][record_id])
        except KeyError:
            raise backend_exceptions.RecordNotFound(
                u'(%s, %s)' % (model_id, record_id)
            )

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

        self._db['models'][model_id] = {
            'definition': deepcopy(definition),
            'permissions': permissions
        }
        if model_id not in self._db['records']:
            self._db['records'][model_id] = {}
        return model_id

    def _record_exists(self, model_id, record_id):
        return record_id in self._db['records'][model_id]

    def _model_exists(self, model_id):
        return model_id in self._db['records']

    def put_record(self, model_id, record, authors, record_id=None):
        doc = {
            'authors': authors,
            'record': record
        }

        if record_id is not None:
            try:
                old_doc = self.__get_raw_record(model_id, record_id)
            except backend_exceptions.RecordNotFound:
                doc['_id'] = record_id
            else:
                old_doc["record"].update(doc["record"])
                doc = old_doc
                doc['authors'] = list(set(authors) | set(old_doc['authors']))
        else:
            key_exist = functools.partial(self._record_exists, model_id)
            record_id = self._generate_id(key_exist=key_exist)
            doc['_id'] = record_id

        self._db['records'][model_id][record_id] = doc
        return record_id

    def delete_record(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        if doc:
            del self._db['records'][model_id][record_id]
        return doc

    def delete_records(self, model_id):
        results = self.get_records(model_id)
        del self._db['records'][model_id]
        return results

    def delete_model(self, model_id):
        records = self.delete_records(model_id)
        doc = self._db['models'][model_id]
        del self._db['models'][model_id]
        return {"definition": doc["definition"],
                "permissions": doc["permissions"],
                "records": records}

    def get_token(self, credentials_id):
        try:
            return str(self._db['tokens'][credentials_id])
        except KeyError:
            raise backend_exceptions.CredentialsNotFound(credentials_id)

    def get_credentials_key(self, credentials_id):
        try:
            return str(self._db['credentials_keys'][credentials_id])
        except KeyError:
            raise backend_exceptions.CredentialsNotFound(credentials_id)

    def store_credentials(self, token, credentials):
        # Check that the token doesn't already exist.
        assert 'id' in credentials and 'key' in credentials
        try:
            self.get_token(credentials['id'])
            raise backend_exceptions.CredentialsAlreadyExist(credentials['id'])
        except backend_exceptions.CredentialsNotFound:
            pass

        self._db['tokens'][credentials['id']] = token
        self._db['credentials_keys'][credentials['id']] = credentials['key']

    def get_model_permissions(self, model_id):
        doc = self.__get_raw_model(model_id)
        return doc['permissions']
