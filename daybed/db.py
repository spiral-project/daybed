from daybed.designdocs import (
    db_model_token,
    db_definition,
    db_data,
    docs
)
from couchdb.design import ViewDefinition


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

    def get_data(self, model_name):
        """Get the definition of the model data.

        :param model_name: the name of the definition you want to retrieve

        """
        return db_data(self.db)[model_name]

    def get_definition_token(self, model_name):
        """Return the token associated with a definition.

        :param model_name: the name of the definition you want to retrieve

        """
        return db_model_token(self.db)[model_name]


def sync_couchdb_views(db):
    """Sync the couchdb documents from python to the server"""
    ViewDefinition.sync_many(db, docs)
