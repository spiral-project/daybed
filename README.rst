Daybed
######

Daybed is a form validation and data storage API, built on top of couchdb.

The basic need is to send model definitions to an API, to then send data
which validates against the specified model definitions.

In term of API access, it means something like this::

    SCHEMA = {
        title: "My super event"
        description: "",
        fields: [
            {
                name: "title",
                type: "string",
                description: "blah",
            },
            {
                name: "category",
                type: "enum",
                description: "blah",
                choices: ('sport', 'culture')
            },
        ],
    }

    > curl -X PUT /definition/events/ -d SCHEMA
    < 200 OK + TOKEN

On the server, we do the validation with colander::

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
    model_definition = Service('Model Definition', '/definition/{modelname}')
    model = Service('Model', '/{modelname}')

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

We can also retireve the definition of the model::

    > HTTP GET /events
    < {
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


Now, what you want is to push some data on the API::

    > HTTP POST /events/
    > DATA = {title: 'djangocong', category: 'geeks'}
    < HTTP 400 'geeks' is not one of 'culture or sports'

Here, the validation failed, let's try again::

    > HTTP POST /events/
    > DATA = {title: 'djangocong', category: 'culture'}
    < 200 + UUID of the created event


To do that, we need this::

    from colander import Invalid

    def schema_validator(request):
        status, resp = conn.GET('/definition/events')
        schema_def = json.loads(resp.body)

        fields = {}

        for field in schema_def.fields:
            if field.type == 'string':
                fields[field.name] = SchemaNode(String())
            elif field.type == 'enum':
                fields[field.name] = SchemaNode(String(), validator=OneOf(field.choices))

        schema = type('Event', (MappingSchema, ), fields)
        try:
            deserialized = schema.deserialize(json.loads(request.body))
        except Invalid e:
            errors = e.get_erroneous_field()
            for error in errors:
                request.errors.add('body', error.name, error.message)


    @model.POST(validators=schema_validator)
    def create_entry(request):
        # unserialize + reserialize the data, adding the "_model" field, and
        # setting it to the name of the model.
        # then send it to the couchdb
        return couchdb status.

We also need a view in the couchdb, to map model names onto docs.

The record is inserted in the db, let's get all the records::

    > HTTP GET /events/
    > Accept: application/json
    < 200 OK
    < DATA = [{title: 'djangocong', category: 'culture'}]

Or individual records::

    > HTTP GET /events/
    > Accept: application/json
    < 200 OK
    < DATA = {title: 'djangocong', category: 'culture'}
