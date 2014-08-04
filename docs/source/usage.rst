How to use the Daybed API
=========================

Daybed is a REST interface you can use to create model definitions, edit them
and publish data that complies to these models.

Let's say we want to have a Daybed-managed *todo list*. Follow the steps and you
will have a grasp of how Daybed works.

To simplify testing, you can use `httpie <https://github.com/jkbr/httpie>`_ in
order to make requests.

All examples in this section are using *httpie* against a local Daybed server
running on port 8000.

In order to authenticate with `Hawk <https://github.com/hueniverse/hawk>`_,
you'll need to install the `requests-hawk module
<https://github.com/mozilla-services/requests-hawk>`_

Authentication
--------------

You need to be authenticated to be able to run most of the commands. In order
to get authenticated, the first thing to do is to get a "token" from Daybed.

This token is a way to identify yourself. A token contains two parts:

1. **a token id** -- Identifier you can publicly share
2. **a secret** -- similar to a password.


In order to get your credentials, you need to send a POST request::

    http POST http://0.0.0.0:8000/tokens

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
        "sessionToken": "ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22"
    }


You can use the returned credentials in your next requests.


Model management
----------------

**PUT and POST /models**


First, we put a definition under the name "todo" using a PUT request
on **/models**::

  http PUT http://localhost:8000/models/todo

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
      }}' > definition

    http PUT http://localhost:8000/models/todo @definition \
         --verbose \
         --auth-type=hawk \
         --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

And we get back::

    HTTP/1.1 200 OK
    Content-Length: 14
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 18:35:10 GMT
    Server: waitress

    {
        "id": "todo"
    }

Note that you could have done this call without being authenticated.

If you use your authentication token, your user will get read *and*
write permissions on the newly created model. The permissions can
be changed later.

In case you don't want to define a name yourself for your model, you can do the
exact same call, replacing the http method from **PUT** to **POST**.
In that case, Daybe will pick a name for your model.


**GET /models**

It return the list of models the user can read the definition::

    http GET http://localhost:8000/models --verbose \
	    --auth-type=hawk \
		--auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    GET /models HTTP/1.1
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



**GET /models/{modelname}**

We can now get our models back::

    http GET http://localhost:8000/models/todo \
      --verbose \
      --auth-type=hawk \
      --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    GET /models/todo HTTP/1.1
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


Depending of the permissions settings, you may get a 401 response
from the server in case you're trying to get the model definition without
the proper authorization.


Pushing data
------------

**POST /models/{modelname}/records**
**PUT /models/{modelname}/records/{id}**

Now that we've defined the schema, we want to push some real data there!::

    http POST http://localhost:8000/models/todo/records item="work on daybed" status="done" \
        --verbose \
        --auth-type=hawk \
        --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    POST /models/todo/records HTTP/1.1
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
    Location: http://localhost:8000/models/todo/records/ebc9f07c8faa4969a76f46b8c514fac6
    Server: waitress

    {
        "id": "ebc9f07c8faa4969a76f46b8c514fac6"
    }

The server sends us back the **id** of the created document.

.. note::
    When you push some data, you can also send a special header, named
    **Validate-Only**, which will allow you to only validate the
    resource you are sending, without actually recording it to the database.


**GET /models/{modelname}/records**

Using the GET method, you can get back the data you have posted::

    http GET http://localhost:8000/models/todo/records \
        --json \
        --verbose \
        --auth-type=hawk \
        --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    GET /models/todo/records HTTP/1.1                                                                                              [5/4051]
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

**GET /models/{modelname}/definition**

::

    http GET http://localhost:8000/models/todo/definition \
        --verbose \
        --auth-type=hawk \
        --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    GET /models/todo/definition HTTP/1.1
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


Manipulating permissions
------------------------

XXX

Get back the model permissions
------------------------------

**GET /models/{modelname}/permissions**

::

    http GET http://localhost:8000/models/todo/permissions \
        --verbose \
        --auth-type=hawk \
        --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    GET /models/todo/permissions HTTP/1.1
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


Add some permissions
--------------------

You can add permissions to an existing *token*, *Authenticated* people or *Everyone*.

As well as tokens, you can define permissions to **system.Authenticated**
and **system.Everyone**, or use their shortcut notation: **Authenticated** and
**Everyone**.

To add `read_definition` and `read_permissions` to Authenticated and remove
`update_permissions` to alexis we would write::

    {
        "Authenticated": ["read_definition", "read_permissions"],
        "alexis": ["-update_permissions"]
    }

For this to be valid, `alexis` must be an existing token.

If you want to add or remove all the permission to/from somebody, you can use the ALL shortcut::

    {
        "Authenticated": ["-ALL"],
        "alexis": ["+ALL"]
    }

If you don't provide the `-` or the `+` in front of the permission we assume you want to add the permission.

This::

    {
        "Authenticated": ["ALL"]
    }

Is equivalent to::

    {
        "Authenticated": ["+ALL"]
    }

In case you try to add a non existing permission or to modify permission of a
non existing token, you will get an error.

If you need to remove permissions from a removed token, you will have to use the PUT endpoint.

**PATCH /models/{modelname}/permissions**

::

   echo '{"Everyone": ["read_definition"]}' | http PATCH http://localhost:8000/models/todo/permissions  \
       --json \
       --verbose \
       --auth-type=hawk \
       --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    PATCH /models/todo/permissions HTTP/1.1
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
            "read_definition"
        ]
    }

**PUT /models/{modelname}/permissions**

This endpoint let you replace a set of permissions for a model. It can be useful if
the PATCH call doesn't work (remove permissions for a removed token.) or to
replace all permissions with one call.


::

   echo '{"Everyone": ["read_definition"], "Authenticated": ["ALL"]}' | http PUT http://localhost:8000/models/todo/permissions \
       --json \
       --verbose \
       --auth-type=hawk \
       --auth='504fd8148d7cdca10baa3c5208b63dc9e13cad1387222550950810a7bdd72d2c:'

    PATCH /models/todo/permissions HTTP/1.1
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


Listing supported fields
------------------------

Daybed supports a bunch of fields. It's easy to add some to your instances.

Sometimes, it can be useful to have a list of these fields. You can get that
list by querying the `/fields` endpoint::

  http GET http://localhost:8000/fields --verbose --json

