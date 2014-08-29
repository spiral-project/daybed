from couchdb.design import ViewDefinition

# Definition of CouchDB design documents, a.k.a. permanent views.

""" Models id."""
models = ViewDefinition('models', 'by_principals', """
function(doc) {
  if (doc.type == "definition") {
    for (var i = 0; i < doc.permissions.read_definition.length; i++) {
      var principal = doc.permissions.read_definition[i];
      emit(principal, doc);
    }
  }
}""")


""" Model definitions, by model id."""
model_definitions = ViewDefinition('definitions', 'all', """
function(doc) {
  if (doc.type == "definition") {
    emit(doc._id, doc);
  }
}""")


""" Model records, by model name."""
records = ViewDefinition('records', 'by_model', """
function(doc) {
  if (doc.type == "record") {
    emit(doc.model_id, doc);
  }
}""")

""" Record, by id."""
records_all = ViewDefinition('records_all', 'all', """
function(doc) {
  if (doc.type == "record") {
    emit(doc._id, doc);
  }
}""")

"""The token from their ids"""
tokens = ViewDefinition('tokens', 'by_name', """
function(doc){
  if(doc.type == 'token'){
      emit(doc.credentials.id, doc);
  }
}
""")


l = locals().values()
docs = [v for v in l if isinstance(v, ViewDefinition)]
