.. _usage-section:

How to use the Daybed API
=========================

Daybed is a REST interface you can use to create model definitions, edit them
and publish data that complies to these models.

Let's say you want to have a Daybed-managed *todo list*. Follow the steps and you
will have a grasp of how Daybed works.

To simplify API calls, you can use `httpie <https://github.com/jkbr/httpie>`_
which performs HTTP requests easily.

All examples in this section are using *httpie* against a local Daybed server
running on port 8000.

Daybed uses `Hawk <https://github.com/hueniverse/hawk>`_, so to run the following
example, you'll need to install the `requests-hawk module
<https://github.com/mozilla-services/requests-hawk>`_.


Listing supported fields
------------------------

Daybed supports several field types to build your model definition. All details
are given in the :ref:`dedicated documentation <fieldtypes-section>` section.

You can also get a list of these fields and their parameters programmatically,
on the `/fields` endpoint::

  http GET http://localhost:8000/v1/fields --verbose --json


Authentication
--------------

You need to be authenticated to be able to run most of the commands. In order
to get authenticated, the first thing to do is to get some :term:`credentials` from Daybed.

In order to get yours, you need to send a ``POST`` request::

    http POST http://localhost:8000/v1/tokens

    HTTP/1.1 201 Created
    Content-Length: 273
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 16:25:49 GMT
    Server: waitress

    {
        "credentials": {
            "algorithm": "sha256",
            "id": "e0394574578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca",
            "key": "416aa1287121218feeb9b751a9614959a1c95fd09aba5959bab7c484dcd1b198"
        },
        "token": "ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22"
    }


In your next requests, you can either :

* use the ``token``, and rely on a Hawk library to wrap everything (*recommended*);
* use the ``credentials`` pair of *id* and *key*, and build the Hawk ``Authorization``
  header yourself (*or probably via ``hawk.js``*).


Model management
----------------

**PUT and POST /v1/models**

You can create models without being authenticated, since model creation is
allowed to everyone by default.

When you are authenticated, all the objects you create will be associated to
your credentials *id*.


First, you put a definition under the name "todo" using a PUT request
on **/models**::

  http PUT http://localhost:8000/v1/models/todo

Use the ``token`` as the ``auth`` value, as expected by the ``requests-hawk``
library.

.. code-block:: bash

    echo '{"definition":
      {
        "title": "todo",
        "description": "A list of my stuff to do",
        "fields": [
            {
                "name": "item",
                "type": "string",
                "label": "The item"
            },
            {
                "name": "status",
                "type": "enum",
                "choices": [
                    "done",
                    "todo"
                ],
                "label": "is it done or not"
            }
         ]
      }
    }' > definition

    http PUT http://localhost:8000/v1/models/todo @definition \
         --verbose \
         --auth-type=hawk \
         --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

And you receive the model id back ::

    HTTP/1.1 200 OK
    Content-Length: 14
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 18:35:10 GMT
    Server: waitress

    {
        "id": "todo"
    }

Since the token was used, the new model was associated to your *id*,
and you are the only one to get read *and* write permissions.
Of course, the model permissions can be changed later.

.. note::

    In case you don't want to define a name yourself for your model,
    you can do the exact same request, replacing the **PUT** http method
    by a **POST**. A random name will be generated.


The definition properties are:

* **title**: The model title
* **description**: The model description
* **fields**: The model fields' list. See :ref:`fields documentation <fieldtypes-section>`
* **extra**: An optional property to store custom data to your model.


**GET /models**

Returns the list of models where you have the permission to read the definition::

    http GET http://localhost:8000/v1/models --verbose \
        --auth-type=hawk \
        --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    GET /v1/models HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="3NXv...=", hash="B0we...=", id="36...0", ts="1407166852", nonce="tQlJHv"
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0


    HTTP/1.1 200 OK
    Content-Length: 202
    Content-Type: application/json; charset=UTF-8
    Date: Mon, 04 Aug 2014 15:40:52 GMT
    Server: waitress

    {
        "models": [
            {
                "description": "A list of my stuff to do.",
                "id": "todo",
                "title": "Todo"
            }
        ]
    }



**GET /v1/models/{modelname}**

You can now get your models back::

    http GET http://localhost:8000/v1/models/todo \
      --verbose \
      --auth-type=hawk \
      --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    GET /v1/models/todo HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="CEhSQuh8tqGY8RbdrnMvGyIRJBDmdxJeu2/HIRB0pbQ=", hash="B0weSUXsMcb5UhL41FZbrUJCAotzSI3HawE1NPLRUz8=", id="e03945
    74578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca", ts="1406228025", nonce="4sEpMQ"
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0



    HTTP/1.1 200 OK
    Content-Length: 1330
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 18:53:45 GMT
    Server: waitress

    {
        "permissions": {
            "e0394574578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca": [
                'create_record',
                'delete_all_records',
                'delete_model',
                'delete_own_records',
                'read_permissions',
                'read_all_records',
                'read_definition',
                'read_own_records',
                'update_permissions',
                'update_all_records',
                'update_definition',
                'update_own_records',
            ]
        },
        "definition": [
            {
                "description": "A list of my stuff to do",
                "fields": [
                    {
                        "label": "The item",
                        "name": "item",
                        "type": "string"
                    },
                    {
                        "choices": [
                            "done",
                            "todo"
                        ],
                        "label": "is it done or not",
                        "name": "status",
                        "type": "enum"
                    }
                ],
                "title": "todo"
            }
        ],
        "records": []
    }


.. note::

    You will get a ``401 - Unauthorized`` response if you don't have the
    permission to read the model definition.


Pushing records
---------------

**POST /v1/models/{modelname}/records**

**PUT /v1/models/{modelname}/records/{id}**

Now that you've defined the schema, you may want to push some real record there::

    http POST http://localhost:8000/v1/models/todo/records item="work on daybed" status="done" \
        --verbose \
        --auth-type=hawk \
        --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    POST /v1/models/todo/records HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="4Sly1HVkkKsRk43dHOLw/e/AmWeoDEe9ZbVu9cugzg0=", hash="KE3ivKqZxHPTg1yzUAJHOu/PYiYWvEoh3SZxzYshikw=", id="e03945
    74578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca", ts="1406228375", nonce="T2NP4V"
    Content-Length: 44
    Content-Type: application/json; charset=utf-8
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0

    {
        "item": "work on daybed",
        "status": "done"
    }

    HTTP/1.1 201 Created
    Content-Length: 42
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 18:59:35 GMT
    Location: http://localhost:8000/v1/models/todo/records/ebc9f07c8faa4969a76f46b8c514fac6
    Server: waitress

    {
        "id": "ebc9f07c8faa4969a76f46b8c514fac6"
    }

The server sends us back the **id** of the newly created record.

.. note::
    You can also only validate the data your are sending, by setting the
    ``Validate-Only`` header, which will prevent storing it as a record.


**GET /v1/models/{modelname}/records**

Using the GET method, you can get back all the records you have created::

    http GET http://localhost:8000/v1/models/todo/records \
        --json \
        --verbose \
        --auth-type=hawk \
        --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    GET /v1/models/todo/records HTTP/1.1                                                                                              [5/4051]
    Accept: application/json
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="OQ9PYGfLhE7L0TPHFpYteHI0j3PBnKgEjyYjMQXMsaM=", hash="NVuBm+XMyya3Tq4EhpZ0cQWjVUyIA8sKnySkKDOIM4M=", id="e0394574578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca", ts="1406232484", nonce="_m0VvY"
    Content-Type: application/json; charset=utf-8
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0


    HTTP/1.1 200 OK
    Content-Length: 151
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 20:08:04 GMT
    Server: waitress

    {
        "records": [
            {
                "item": "work on daybed",
                "status": "done"
            },
        ]
    }



Get back a definition
---------------------

**GET /v1/models/{modelname}/definition**

::

    http GET http://localhost:8000/v1/models/todo/definition \
        --verbose \
        --auth-type=hawk \
        --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    GET /v1/models/todo/definition HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="k9edIqpoz7cSUJQTroXgM4vgDoZb2Z2KO2u40QCbtYk=", hash="B0weSUXsMcb5UhL41FZbrUJCAotzSI3HawE1NPLRUz8=", id="220a1c4212d8f005f0f56191c5a91f8fe266282d38b042e6b35cad8034f22871", ts="1406645426", nonce="meNBWv"
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0


    HTTP/1.1 200 OK
    Content-Length: 224
    Content-Type: application/json; charset=UTF-8
    Date: Tue, 29 Jul 2014 14:50:26 GMT
    Server: waitress

    {
        "description": "A list of my stuff to do",
        "fields": [
            {
                "label": "The item",
                "name": "item",
                "type": "string"
            },
            {
                "choices": [
                    "done",
                    "todo"
                ],
                "label": "is it done or not",
                "name": "status",
                "type": "enum"
            }
        ],
        "title": "todo"
    }


Get back the model permissions
------------------------------

**GET /v1/models/{modelname}/permissions**

::

    http GET http://localhost:8000/v1/models/todo/permissions \
        --verbose \
        --auth-type=hawk \
        --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    GET /v1/models/todo/permissions HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="G8PntYqGA0DiP4EC0qvvr70tmCZrsVBdTTTBq9ZeKYg=", hash="B0weSUXsMcb5UhL41FZbrUJCAotzSI3HawE1NPLRUz8=", id="220a1c4212d8f005f0f56191c5a91f8fe266282d38b042e6b35cad8034f22871", ts="1406645480", nonce="4D0z9n"
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0


    HTTP/1.1 200 OK
    Content-Length: 293
    Content-Type: application/json; charset=UTF-8
    Date: Tue, 29 Jul 2014 14:51:20 GMT
    Server: waitress

    {
        "220a1c4212d8f005f0f56191c5a91f8fe266282d38b042e6b35cad8034f22871": [
            "create_record",
            "delete_all_records",
            "delete_model",
            "delete_own_records",
            "read_all_records",
            "read_definition",
            "read_own_records",
            "read_permissions",
            "update_all_records",
            "update_definition",
            "update_own_records"
            "update_permissions",
        ]
    }

Change model permissions
------------------------

As described in :ref:`the dedicated section about permissions <permissions-section>`,
you can add or remove permissions from models.

For example, you may want to give the permission to read everyone's records
to anonymous users (i.e. *Everyone*).

Using a ``PATCH`` request, existing permissions configuration is not overwritten
completely :

**PATCH /v1/models/{modelname}/permissions**

::

   echo '{"Everyone": ["+read_all_records"]}' | http PATCH http://localhost:8000/v1/models/todo/permissions  \
       --json \
       --verbose \
       --auth-type=hawk \
       --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    PATCH /v1/models/todo/permissions HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="CWT9du2YxOoTb2i5d15bBTA4XiSYY/99ybh6g7welLM=", hash="Nt8m2h1nc5lVUItOobOliVj6hul0FYXmwpEmkjyp+WU=", id="220a1c4212d8f005f0f56191c5a91f8fe266282d38b042e6b35cad8034f22871", ts="1406645940", nonce="2il3kl"
    Content-Length: 34
    Content-Type: application/json; charset=utf-8
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0

    {
        "Everyone": [
            "+read_all_records"
        ]
    }

    HTTP/1.1 200 OK
    Content-Length: 333
    Content-Type: application/json; charset=UTF-8
    Date: Tue, 29 Jul 2014 14:59:00 GMT
    Server: waitress

    {
        "220a1c4212d8f005f0f56191c5a91f8fe266282d38b042e6b35cad8034f22871": [
            "create_record",
            "delete_all_records",
            "delete_model",
            "delete_own_records",
            "read_all_records",
            "read_definition",
            "read_own_records",
            "read_permissions",
            "update_all_records",
            "update_definition",
            "update_own_records"
            "update_permissions",
        ],
        "system.Everyone": [
            "read_all_records"
        ]
    }

If you add an unknown permission or modify the permissions of an unknown *id*,
you will get an error.


Reset permissions
-----------------

Using a ``PUT`` request, existing permissions will be completely erased and
replaced by the new ones.

Using the ``ALL`` shortcut, you can grant all available permissions.

**PUT /v1/models/{modelname}/permissions**

::

   echo '{"Everyone": ["read_definition"], "Authenticated": ["ALL"]}' | http PUT http://localhost:8000/v1/models/todo/permissions \
       --json \
       --verbose \
       --auth-type=hawk \
       --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    PATCH /v1/models/todo/permissions HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate
    Authorization: Hawk mac="CWT9du2YxOoTb2i5d15bBTA4XiSYY/99ybh6g7welLM=", hash="Nt8m2h1nc5lVUItOobOliVj6hul0FYXmwpEmkjyp+WU=", id="220a1c4212d8f005f0f56191c5a91f8fe266282d38b042e6b35cad8034f22871", ts="1406645940", nonce="2il3kl"
    Content-Length: 34
    Content-Type: application/json; charset=utf-8
    Host: localhost:8000
    User-Agent: HTTPie/0.8.0

    {
        "Everyone": [
            "read_definition"
        ],
        "Authenticated": [
            "ALL"
        ]
    }

    HTTP/1.1 200 OK
    Content-Length: 333
    Content-Type: application/json; charset=UTF-8
    Date: Tue, 29 Jul 2014 14:59:00 GMT
    Server: waitress

    {
        "system.Authenticated": [
            "create_record",
            "delete_all_records",
            "delete_model",
            "delete_own_records",
            "read_all_records",
            "read_definition",
            "read_own_records",
            "read_permissions",
            "update_all_records",
            "update_definition",
            "update_own_records"
            "update_permissions",
        ],
        "system.Everyone": [
            "read_definition"
        ]
    }


.. note::

    It can be useful if you need to remove permissions associated to an unknown
    *id* for example.
