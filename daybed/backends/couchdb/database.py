from . import views
from uuid import uuid4


class Database(object):
    """Object handling all the connections to the couchdb server."""

    def __init__(self, db):
        self._db = db

    def get_model_definition(self, model_id):
        results = views.model_definitions(self._db)[model_id].rows
        for result in results:
            return result.value

    def get_data_items(self, model_id):
        return views.model_data(self._db)[model_id]

    def get_data_item(self, model_id, data_item_id):
        key = '-'.join((model_id, data_item_id))
        data_items = views.model_data_items(self._db)[key]
        if len(data_items):
            data_item = data_items.rows[0].value
            return data_item
        return None

    def put_model_definition(self, model_id, definition):
        data_id, _ = self._db.save({
            'type': 'definition',
            '_id': model_id,
            'definition': definition,
            })
        return data_id

    def put_data_item(self, model_id, data, data_item_id=None):
        doc = {
            'type': 'data',
            'data': data,
            'model_id': model_id}

        if data_item_id is not None:
            old_doc = self.get_data_item(model_id, data_item_id)
            old_doc.update(doc)
            doc = old_doc
        else:
            data_item_id = str(uuid4()).replace('-', '')
            doc['_id'] = '-'.join((model_id, data_item_id))

        self._db.save(doc)
        return data_item_id

    def delete_data_item(self, model_id, data_item_id):
        doc = self.get_data_item(model_id, data_item_id)
        if doc:
            self._db.delete(doc)
        return doc

    def delete_data_items(self, model_id):
        results = views.model_data(self._db)[model_id].rows
        for result in results:
            self._db.delete(result.value)
        return results

    def delete_model(self, model_id):
        """DELETE ALL THE THINGS"""

        # delete the associated data if any
        self.delete_data_items(model_id)

        # delete the model definition
        doc = views.model_definitions(self._db)[model_id].rows[0].value
        if doc:
            self._db.delete(doc)
        return doc
