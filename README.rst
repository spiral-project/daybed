The basic need is to send a model definition to an API, and then send data
which validates against the model definition.

In term of API access, this means something like this::

    SCHEMA = {
        "title": "My super event"
        "description": "", 
        "fields": [
            {
                "name": "title", 
                "type": "string",
                "description": "blah",
            }, 
            {
                "name": "category", 
                "type": "enum",
                "description": "blah",
                "choices": ('sport', 'culture')
            }, 
        ], 
    }

    > curl -X PUT /events/ -d SCHEMA
    < 200 OK + TOKEN

On the server, we do the validation with cornice + colander::

    class ModelDefinition(MappingSchema):
        title = SchemaNode(String())
        description = SchemaNode(String())
        fields = SequenceSchema(ModelField())

    class ModelField(MappingSchema):
        name = SchemaNode(String())
        type = SchemaNode(String(), validator=OneOf(('int, 'string', 'enum'))
        description = SchemaNode(String())
        # TBD in subclassing, a way to have optional fields. Cross Field ?
        choices = SequenceSchema(String())


View in pyramid::

    from cornice import Service
    model_definition = Service('Model Definition', '/{modelname}')

    @model_definition.PUT(schema=ModelDefinition())
    def create_model_definition(request):
        con = couchdb.get_connection()
        modelname = request.matchdict['modelname']
        token = con.get(uri='tokens/{modename}'.format(request.matchdict))
        if token:
            if token is not request.GET['token']:
                return request.errors.add('body', 'token', 'the token is not valid')
        else:
            # Generate a token with uuid
            token = con.put(uri='tokens/{modelname}'.format(request.matchdict), uuid.gen())

        con.put(uri=modelname, data=request.body)  # save to couchdb
        return {'token': token}

    
If you want to update the schema, you need to add the "token" you received
during the creation of the model definition::

    > curl -X PUT /events/?token=<yourtoken> -d SCHEMA
    < 200 OK + TOKEN (the same one)


Now, what you want is to push some data on the API::

    > HTTP POST /events/
    > DATA = {title: 'djangocong', category: 'geeks'}
    < HTTP 400 'geeks' is not one of 'culture or sports'

Here, the validation failed, let's try again::

    > HTTP POST /events/
    > DATA = {title: 'djangocong', category: 'culture'}
    < 200 + UUID of the created event

The record is inserted in the db, let's get all the records::

    > HTTP GET /events/
    > Accept: application/json
    < 200 OK
    < DATA = {title: 'djangocong', category: 'culture'}
