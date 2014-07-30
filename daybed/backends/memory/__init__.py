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

    def __get_raw_model(self, model_id):
        try:
            return deepcopy(self._db['models'][model_id])
        except KeyError:
            raise ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_raw_model(model_id)['definition']

    def __get_raw_records(self, model_id):
        # Check that model_id exists and raises if not.
        self.__get_raw_model(model_id)
        return self._db['records'].get(model_id, {}).values()

    def get_records(self, model_id, with_authors=False):
        records = []
        for item in self.__get_raw_records(model_id):
            item['record']['id'] = item['_id']
            if with_authors:
                records.append({"authors": deepcopy(item['authors']),
                                "record": deepcopy(item['record'])})
            else:
                records.append(deepcopy(item['record']))
        return records

    def __get_raw_record(self, model_id, record_id):
        try:
            return deepcopy(self._db['records'][model_id][record_id])
        except KeyError:
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

        self._db['models'][model_id] = {
            'definition': definition,
            'acls': acls,
        }
        self._db['records'][model_id] = {}
        return model_id

    def put_record(self, model_id, record, authors, record_id=None):
        doc = {
            'authors': authors,
            'record': record
        }

        if record_id is not None:
            try:
                old_doc = self.__get_raw_record(model_id, record_id)
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
        doc = self.__get_raw_record(model_id, record_id)
        if doc:
            del self._db['records'][model_id][record_id]
        return doc

    def delete_records(self, model_id):
        results = self.__get_raw_records(model_id)
        records_ids = [r['_id'] for r in results]
        for record_id in records_ids:
            self.delete_record(model_id, record_id)
        return results

    def delete_model(self, model_id):
        self.delete_records(model_id)
        doc = self._db['models'][model_id]
        del self._db['models'][model_id]
        return doc

    def get_token(self, tokenHmacId):
        try:
            return str(self._db['tokens'][tokenHmacId])
        except KeyError:
            raise TokenNotFound(tokenHmacId)

    def add_token(self, tokenHmacId, secret):
        # Check that the token doesn't already exist.
        try:
            self.get_token(tokenHmacId)
            raise TokenAlreadyExist(tokenHmacId)
        except TokenNotFound:
            pass

        self._db['tokens'][tokenHmacId] = secret

    def get_model_acls(self, model_id):
        doc = self.__get_raw_model(model_id)
        return doc['acls']
