from daybed.designdocs import (
    db_model_token,
    db_model_definition,
    db_model_data,
    docs
)
from couchdb.design import ViewDefinition


class DatabaseConnection(object):
    """Object handling all the connections to the couchdb server."""

    def __init__(self, db):
        self.db = db
        self.save = db.save

    def get_model_definition(self, modelname):
        """Get the scheme definition from the modelname.

        :param modelname: the name of the definition you want to retrieve

        """
        results = db_model_definition(self.db)[modelname]
        for result in results:
            return result.value

    def get_model_data(self, modelname):
        """Get the definition of the model data.

        :param modelname: the name of the definition you want to retrieve

        """
        return db_model_data(self.db)[modelname]

    def get_definition_token(self, modelname):
        """Return the token associated with a definition.

        :param modelname: the name of the definition you want to retrieve

        """
        return db_model_token(self.db)[modelname]


def sync_couchdb_views(db):
    """Sync the couchdb documents from python to the server"""
    ViewDefinition.sync_many(db, docs)
