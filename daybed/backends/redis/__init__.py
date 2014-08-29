import json
import redis

from daybed.backends import exceptions as backend_exceptions


class RedisBackend(object):

    @classmethod
    def load_from_config(cls, config):
        settings = config.registry.settings
        generator = config.maybe_dotted(settings['daybed.id_generator'])
        return RedisBackend(
            settings.get('backend.db_host', 'localhost'),
            settings.get('backend.db_port', 6379),
            settings.get('backend.db_index', 0),
            generator(config)
        )

    def __init__(self, host, port, db, id_generator):
        self._db = redis.StrictRedis(host=host, port=port, db=db)

        # Ping the server to be sure the connection works.
        self._db.ping()
        self._generate_id = id_generator

    def delete_db(self):
        self._db.flushdb()

    def get_models(self, principals):
        principals = set(principals)
        models_id = self._db.keys("model.*")
        if models_id:
            models = [json.loads(m.decode("utf-8"))
                      for m in self._db.mget(*models_id) if m]
            return [{"id": m['id'],
                     "title": m['definition']['title'],
                     "description": m['definition']['description']}
                    for m in models if principals.intersection(
                        m['permissions']['read_definition']) != set()]
        else:
            return []

    def __get_raw_model(self, model_id):
        model = self._db.get("model.%s" % model_id)
        if model is not None:
            return json.loads(model.decode("utf-8"))
        raise backend_exceptions.ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        model = self.__get_raw_model(model_id)
        return model['definition']

    def get_model_permissions(self, model_id):
        doc = self.__get_raw_model(model_id)
        return doc['permissions']

    def __get_raw_records(self, model_id):
        # Check if the model still exists or raise
        self.__get_raw_model(model_id)

        model_records = self._db.smembers(
            "modelrecords.%s" % model_id
        )
        if model_records:
            return [json.loads(i.decode("utf-8"))
                    for i in self._db.mget(*model_records)]
        else:
            return []

    def get_records(self, model_id, raw_records=None):
        return [r["record"] for r in
                self.get_records_with_authors(model_id, raw_records)]

    def get_records_with_authors(self, model_id, raw_records=None):
        if raw_records is None:
            raw_records = self.__get_raw_records(model_id)
        records = []
        for item in self.__get_raw_records(model_id):
            records.append({"authors": item["authors"],
                            "record": item["record"]})
        return records

    def __get_raw_record(self, model_id, record_id):
        record = self._db.get("modelrecord.%s.%s" % (model_id, record_id))
        if record is not None:
            return json.loads(record.decode("utf-8"))
        raise backend_exceptions.RecordNotFound(
            u'(%s, %s)' % (model_id, record_id)
        )

    def get_record(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        return doc['record']

    def get_record_authors(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        return doc['authors']

    def put_model(self, definition, permissions, model_id=None):
        if model_id is None:
            model_id = self._generate_id()

        self._db.set(
            "model.%s" % model_id,
            json.dumps({
                'id': model_id,
                'definition': definition,
                'permissions': permissions
            })
        )
        return model_id

    def put_record(self, model_id, record, authors, record_id=None):
        doc = {
            'authors': authors,
            'record': record
        }

        if record_id is not None:
            try:
                old_doc = self.__get_raw_record(model_id, record_id)
            except backend_exceptions.RecordNotFound:
                pass
            else:
                authors = list(set(authors) | set(old_doc['authors']))
                doc['authors'] = authors
                old_doc.update(doc)
                doc = old_doc
        else:
            record_id = self._generate_id()

        doc['record']['id'] = record_id
        self._db.set(
            "modelrecord.%s.%s" % (model_id, record_id),
            json.dumps(doc)
        )
        self._db.sadd(
            "modelrecords.%s" % model_id,
            "modelrecord.%s.%s" % (model_id, record_id)
        )
        return record_id

    def delete_record(self, model_id, record_id):
        doc = self.__get_raw_record(model_id, record_id)
        if doc:
            self._db.delete("modelrecord.%s.%s" % (model_id, record_id))
            self._db.srem(
                "modelrecords.%s" % model_id,
                "modelrecord.%s.%s" % (model_id, record_id)
            )
            return doc

    def delete_records(self, model_id):
        records = self.get_records(model_id)
        existing_records_keys = [
            "modelrecord.%s.%s" % (model_id, r["id"]) for r in records
        ]
        existing_records_keys.append("modelrecords.%s" % model_id)

        self._db.delete(*existing_records_keys)
        return records

    def delete_model(self, model_id):
        doc = self.__get_raw_model(model_id)
        doc["records"] = self.delete_records(model_id)
        self._db.delete("model.%s" % model_id)
        return {
            "definition": doc["definition"],
            "records": doc["records"],
            "permissions": doc["permissions"]
        }

    def get_token(self, credentials_id):
        """Retrieves a token by its id"""
        token = self._db.get("token.%s" % credentials_id)
        if token is None:
            raise backend_exceptions.CredentialsNotFound(credentials_id)
        return token.decode("utf-8")

    def get_credentials_key(self, credentials_id):
        """Retrieves a token by its id"""
        credentials_key = self._db.get("credentials_key.%s" % credentials_id)
        if credentials_key is None:
            raise backend_exceptions.CredentialsNotFound(credentials_id)
        return credentials_key.decode("utf-8")

    def store_credentials(self, token, credentials):
        # Check that the token doesn't already exist.
        assert 'id' in credentials and 'key' in credentials
        try:
            self.get_token(credentials['id'])
            raise backend_exceptions.CredentialsAlreadyExist(credentials['id'])
        except backend_exceptions.CredentialsNotFound:
            pass

        self._db.set("token.%s" % credentials['id'], token)
        self._db.set("credentials_key.%s" % credentials['id'],
                     credentials['key'])
