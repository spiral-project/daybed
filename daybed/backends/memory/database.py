from copy import deepcopy


class Database(object):
    """Object handling all the connections to the couchdb server."""

    def __init__(self, db, generate_id):
        self._db = db
        self.generate_id = generate_id

    def get_model_definition(self, model_id):
        if model_id in self._db['models']:
            return deepcopy(self._db['models'][model_id])

    def put_model_definition(self, definition, model_id=None):
        if model_id is None:
            model_id = self.generate_id()

        self._db['models'][model_id] = {
            '_id': model_id,
            'definition': definition,
        }
        self._db['data'][model_id] = {}
        return model_id

    def delete_model(self, model_id):
        if model_id in self._db['models']:
            del self._db['models'][model_id]
        if model_id in self._db['data']:
            del self._db['data'][model_id]

    def get_data_items(self, model_id):
        return [deepcopy(value)
                for value in self._db['data'].get(model_id, {}).values()]

    def get_data_item(self, model_id, data_item_id):
        if model_id in self._db['data'] and \
           data_item_id in self._db['data'][model_id]:
            return deepcopy(self._db['data'][model_id][data_item_id])

    def put_data_item(self, model_id, data, data_item_id=None):
        if data_item_id is None:
            data_item_id = self.generate_id()
            self._db['data'][model_id][data_item_id] = {
                '_id': data_item_id,
                'data': data
            }
        else:
            self._db['data'][model_id][data_item_id].update({
                'data': data
            })

        return data_item_id

    def delete_data_item(self, model_id, data_item_id):
        if model_id in self._db['data'] and \
           data_item_id in self._db['data'][model_id]:
            del self._db['data'][model_id][data_item_id]
            return True
