from copy import deepcopy

from daybed.backends.exceptions import (
    TokenAlreadyExist, TokenNotFound, ModelNotFound, RecordNotFound
)


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
            'acls': {},
            'tokens': {}
        }

    def __get_model(self, model_id):
        try:
            return deepcopy(self._db['models'][model_id])
        except KeyError:
            raise ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_model(model_id)['definition']

    def __get_records(self, model_id):
        # Check that model_id exists and raises if not.
        self.__get_model(model_id)
        return self._db['records'].get(model_id, {}).values()

    def get_records(self, model_id):
        records = []
        for item in self.__get_records(model_id):
            item['record']['id'] = item['_id']
            records.append(deepcopy(item['record']))
        return records

    def __get_record(self, model_id, record_id):
        try:
            return deepcopy(self._db['records'][model_id][record_id])
        except KeyError:
            raise RecordNotFound(u'(%s, %s)' % (model_id, record_id))

    def get_record(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        return doc['record']

    def get_record_authors(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        return doc['authors']

    def put_model(self, definition, acls, model_id=None):
        if model_id is None:
            model_id = self._generate_id()

        self._db['models'][model_id] = {
            'type': 'definition',
            '_id': model_id,
            'definition': definition,
            'acls': acls,
        }
        self._db['records'][model_id] = {}
        return model_id

    def put_record(self, model_id, record, authors, record_id=None):
        doc = {
            'type': 'record',
            'authors': authors,
            'model_id': model_id,
            'record': record
        }

        if record_id is not None:
            try:
                old_doc = self.__get_record(model_id, record_id)
            except RecordNotFound:
                doc['_id'] = record_id
            else:
                authors = list(set(authors) | set(old_doc['authors']))
                doc['authors'] = authors
                old_doc.update(doc)
                doc = old_doc
        else:
            record_id = self._generate_id()
            doc['_id'] = record_id

        self._db['records'][model_id][record_id] = doc
        return record_id

    def delete_record(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        if doc:
            del self._db['records'][model_id][record_id]
        return doc

    def delete_records(self, model_id):
        results = self.__get_records(model_id)
        records_ids = [r['_id'] for r in results]
        for record_id in records_ids:
            self.delete_record(model_id, record_id)
        return results

    def delete_model(self, model_id):
        self.delete_records(model_id)
        doc = self._db['models'][model_id]
        del self._db['models'][model_id]
        return doc

    def __get_token(self, token):
        try:
            return deepcopy(self._db['tokens'][token])
        except KeyError:
            raise TokenNotFound(token)

    def get_token(self, token):
        """Returns the information associated with an token"""
        token = self.__get_token(token)
        return token['token']

    def add_token(self, token):
        # Check that the token doesn't already exist.
        try:
            token = token['name']
            token = self.__get_token(token)
            raise TokenAlreadyExist(token)
        except TokenNotFound:
            pass

        token = token.copy()

        doc = dict(token=token, name=token, type='token')
        self._db['tokens'][token] = doc
        return token

    def get_model_acls(self, model_id):
        doc = self.__get_model(model_id)
        return doc['acls']
