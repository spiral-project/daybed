from . import views


class Database(object):
    """Object handling all the connections to the couchdb server."""

    def __init__(self, db, generate_id):
        self._db = db
        self.generate_id = generate_id

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

    def put_model(self, definition, users, policy_id, model_id=None):
        if model_id is None:
            model_id = self.generate_id()

        definition_id, _ = self._db.save({
            'type': 'definition',
            '_id': model_id,
            'definition': definition,
            'users': users,
            'policy_id': policy_id
            })
        return definition_id

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
            data_item_id = self.generate_id()
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

    def get_roles(self, model_id):
        return {'admins': ['group:pirates', 'group:flibustiers'],
                'users': ['Remy', 'Alexis']}

    def get_groups(self, user):
        return ['pirates', 'bartender']

    def get_policy(self, policy_name):
        return views.policy_doc(self._db)[policy_name].rows[0].value

    def get_model_policy(self, model_id):
        policy_name = views.model(self._db)[model_id].rows[0].value['policy']
        return self.get_policy(policy_name)
