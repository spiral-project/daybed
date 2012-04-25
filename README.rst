Daybed
######

Daybed is a form validation and data storage API, built on top of couchdb.

The basic need is to send model definitions to an API, to then send data
which validates against the specified model definitions.

In term of API access, it means something like this::

    SCHEMA = {
        name: "My super event",
        description: "",
        blah: "toto",
        fields: [
            {
                type: "string",
                name: "title",
                description: "blah",
            },
            {
                input: false,
                type: "header",
                value: "foo",
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

If you want to update the schema, you need to add the "token" you received
during the creation of the model definition::

    > curl -X PUT /events/?token=<yourtoken> -d SCHEMA
    < 200 OK + TOKEN (the same one)

We can also retrieve the definition of the model::

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
