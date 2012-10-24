from couchdb.design import ViewDefinition
from daybed.designdocs import (
    db_model_token,
    db_definition,
    db_data,
    db_data_item,
    docs
)


class DatabaseConnection(object):
    """Object handling all the connections to the couchdb server."""

    def __init__(self, db):
        self.db = db
        self.save = db.save

    def get_definition(self, model_name):
        """Get the scheme definition from the model_name.

        :param model_name: the name of the definition you want to retrieve

        """
        results = db_definition(self.db)[model_name]
        for result in results:
            return result.value

    def get_definition_token(self, model_name):
        """Return the token associated with a definition.

        :param model_name: the name of the definition you want to retrieve

        """
        return db_model_token(self.db)[model_name]

    def get_data(self, model_name):
        """Get the definition of the model data.

        :param model_name: the name of the definition you want to retrieve

        """
        return db_data(self.db)[model_name]

    def get_data_item(self, model_name, data_item_id):
        """Get a data-item and checks it behaves to the requested model"""
        key = [str(data_item_id), str(model_name)]
        data_items = db_data_item(self.db)[key]
        if len(data_items):
            data_item = data_items.rows[0]
            return data_item
        return None

    def create_data(self, model_name, data, data_id=None):
        """Create a data to a model_name."""
        if data_id:
            data_doc = self.db[data_id]
            data_id = data_doc.id
        else:
            data_doc = {
                'type': 'data',
                'model_name': model_name,
            }
        data_doc['data'] = data

        if data_id:
            self.db[data_id] = data_doc
        else:
            data_id, rev = self.db.save(data_doc)

        return data_id


def sync_couchdb_views(db):
    """Sync the couchdb documents from python to the server"""
    ViewDefinition.sync_many(db, docs)
