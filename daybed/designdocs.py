from couchdb.design import ViewDefinition


"""  Definition of CouchDB design documents, a.k.a. permanent views. """
__design_docs__ = []

""" Model definitions, by model name. """
db_model_definition = ViewDefinition('model', 'definition', """function(doc) {
        if (doc.type == "definition") {
            emit(doc.model, doc.definition);
        }
}""")
__design_docs__.append(db_model_definition)

""" Model tokens, by model name. """
db_model_token = ViewDefinition('model', 'token', """function(doc) {
    if (doc.type == "token") {
        emit(doc.model, doc.token);
    }
}""")
__design_docs__.append(db_model_token)

""" Model data, by model name. """
db_model_data = ViewDefinition('model', 'data', """function(doc) {
        if (doc.type == "data") {
            emit(doc.model, doc.data);
        }
}""")
__design_docs__.append(db_model_data)
