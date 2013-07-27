from couchdb.design import ViewDefinition

# Definition of CouchDB design documents, a.k.a. permanent views.


""" Model definitions, by model id. """
model_definitions = ViewDefinition('definitions', 'all',
                                   """function(doc) {
        if (doc.type == "definition") {
            emit(doc._id, doc);
        }
}""")


""" Model data, by model name. """
model_data = ViewDefinition('data_items', 'by_model', """function(doc) {
        if (doc.type == "data") {
            emit(doc.model_id, doc);
        }
}""")

""" Data item, by id. """
model_data_items = ViewDefinition('data_items', 'all', """function(doc) {
        if (doc.type == "data") {
            emit(doc._id, doc);
        }
}""")

docs = [model_definitions, model_data, model_data_items]
