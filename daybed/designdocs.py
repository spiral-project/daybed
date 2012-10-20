from couchdb.design import ViewDefinition


"""  Definition of CouchDB design documents, a.k.a. permanent views. """
docs = []

""" Model definitions, by model name. """
db_model_definition = ViewDefinition('name', 'definition', """function(doc) {
        if (doc.type == "definition") {
            emit(doc.name, doc.definition);
        }
}""")
docs.append(db_model_definition)

""" Model tokens, by model name. """
db_model_token = ViewDefinition('name', 'token', """function(doc) {
    if (doc.type == "definition") {
        emit(doc.name, doc.token);
    }
}""")
docs.append(db_model_token)

""" Model data, by model name. """
db_model_data = ViewDefinition('model_name', 'data', """function(doc) {
        if (doc.type == "data") {
            emit(doc.model_name, doc.data);
        }
}""")
docs.append(db_model_data)
