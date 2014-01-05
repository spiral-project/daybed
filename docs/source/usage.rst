=========================
How to use the daybed API
=========================

Daybed is a REST interface you can use to create definitions, edit them and
publish data that complies to these models.

Let's say we want to have a daybed managed todo list. First, we put
a definition under the name "todo".


Authentication
--------------

You need to be authenticated to be able to run this curl commands.

You can use REST Console in Chrome to use your Persona credentials.

I command line, you will have to use the BasicAuthAuthenticationPolicy
backend, you can add `` -u admin@example.com:apikey`` to each curl
request to get rid of the 403 error.


Model management
----------------

**PUT /models**

We want to push this to daybed, if we run it locally, that would be something
like this:

.. code-block:: bash

    model='{
      "definition": {
        "title": "todo",
        "description": "A list of my stuff to do", 
        "fields": [
            {
                "name": "item", 
                "type": "string",
                "description": "The item"
            }, 
            {
                "name": "status", 
                "type": "enum",
                "choices": [
                    "done", 
                    "todo"
                ], 
                "description": "is it done or not"
            }
         ]
      }
    }'

    curl -XPUT http://localhost:8000/models/todo -d "${model}" -u admin@example.com:apikey

And we get back::

    {"id": "todo"}

**GET /models**

We can now get our models back::

    curl http://localhost:8000/models/todo -u admin@example.com:apikey | python -m json.tool

    {
        "definition": [{
            "fields": [{
                "type": "string",
                "name": "item",
                "description": "The item"
            }, {
                "choices": ["done", "todo"],
                "type": "enum",
                "description": "is it done or not",
                "name": "status"
            }],
            "description": "A list of my stuff to do",
            "title": "todo"
        }],
        "data": [],
        "roles": {
            "admins": ["admin@example.com"]
        },
        "policy_id": "read-only"
    }

**POST /models**

We can also post on ``http://localhost:8000/models`` and we get back an id::

    curl -XPOST http://localhost:8000/models -d "${model}" -u admin@example.com:apikey

    {
        "id": "a8e6c80dcd3b4aeb847b423ffc399fcc"
    }


Pushing data
------------

**POST /models/{modelname}/data**
**PUT /models/{modelname}/data/{id}**

Now that we defined the schema, we want to push some real data there::

    data='{"item": "finish the documentation", "status": "todo"}'
    curl -XPOST http://localhost:8000/models/todo/data -d "$data" -u admin@example.com:apikey

And we get this in exchange, which is the id of the created document.::

    {"id": "c429ab7c1f0f49a99cade9b76b9e6311"}

.. note::
    When you push some data, you can also send a special header, named
    `X-Daybed-Validate-Only`, which will allow you to only validate the
    resource you are sending, without actually recording it to the database.

**GET /models/{modelname}/data/{id}**

Using the GET method, you can get back the data you just POST::

    curl http://localhost:8000/models/todo/data/c429ab7c1f0f49a99cade9b76b9e6311 -u admin@example.com:apikey

    {
        "status": "todo",
        "item": "finish the documentation"
    }


Get back a definition
---------------------

**GET /models/{modelname}/definition**

::

    curl http://localhost:8000/models/todo/definition -u admin@example.com:apikey | python -m json.tool

    {
        "description": "A list of my stuff to do", 
        "fields": [
            {
                "description": "The item", 
                "name": "item", 
                "type": "string"
            }, 
            {
                "choices": [
                    "done", 
                    "todo"
                ], 
                "description": "is it done or not", 
                "name": "status", 
                "type": "enum"
            }
        ], 
        "title": "todo"
    }


Get back all the data you pushed to a model
-------------------------------------------

**GET /models/{modelname}/data**

::

    curl http://localhost:8000/models/todo/data -u admin@example.com:apikey | python -m json.tool

    {
        "data": [{
            "status": "todo",
            "item": "finish the documentation",
            "id": "c429ab7c1f0f49a99cade9b76b9e6311"
        }]
    }

Get policy list
---------------

**GET /policies**

::

    curl http://localhost:8000/policies

    {'policies': ["read-only"]}

**GET /policies/{policy_name}**

::

    curl http://localhost:8000/policies/read-only

    {
        "role:admins": 65535,
        "system.Authenticated": 32768,
        "system.Everyone": 17408
    }

This means::

    {
        "role:admins": 0xFFFF,
        "system.Authenticated": 0xC000,
        "system.Everyone": 0x4400
    }

 - People with the role admins, can do everything on the model and it data.
 - Other people can read Definition and Data but not Users and Policy

+-----------------+------------+------+--------+--------+
| Right example   | Definition | Data | Users  | Policy |
+=================+============+======+========+========+
| 0xFFFF - 65535  |    CRUD    | CRUD |  CRUD  |  CRUD  |
+-----------------+------------+------+--------+--------+
| 0xC000 - 32768  |    CR      |      |        |        |
+-----------------+------------+------+--------+--------+
| 0x4400 - 17408  |     R      |  R   |        |        |
+-----------------+------------+------+--------+--------+
