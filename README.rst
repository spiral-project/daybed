Daybed
######

Daybed is a form validation and data storage API, built on top of couchdb.
In other words, it's a way to create definitions (models), do validation from
here and filter the results.

Why ?
=====

Maybe do you know google forms? It let you define a model and generate a form
from it. Then users without any computer knowledge will use this form to
submit information which will then be available into a spreadsheet.

That's working out pretty well, but tied you to the Google services. There are
several issues to this: you can't change the way the google API work to match
your needs and you need to let google store all this information on their
server, and accept their terms of service.

As a data geek and librist, I don't think that's a reasonable choice.

**Daybed** tries to solve this by providing a REST API able to do validation
for you, depending on some rules you defined, and it is a free software, so you
can modify it if you want / need.

Okay, what does it looks like, then?
====================================

Daybed is basically a REST interface to create models, edit them and publish
data that complies to these models.

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

Hacking daybed
--------------

Daybed comes with a Makefile to simplify your life when developing. To install
your virtual environment and get started, you need to type::

    make setup_venv

Then, running the test suite is a good way to check that everything is going
well, and is well installed. You can run them with `make tests`.

Once everything is okay, you can run the server with `make serve`.
