How to use the daybed API
=========================

Daybed is a REST interface you can use to create definitions, edit them and
publish data that complies to these models.

Let's say we want to have a daybed-managed todo list. Follow the steps and you
will have a grasp of how daybed works.

To ease testing, you can use `httpie <https://github.com/jkbr/httpie>`_ in
order to make requests. Examples of use with httpie are provided when possible.


In order to authenticate with `Hawk <https://github.com/hueniverse/hawk>`_,
you'll need to install the `requests-hawk module
<https://github.com/mozilla-services/requests-hawk>`_

Authentication
--------------

You need to be authenticated to be able to run most of the commands. In order
to get authenticated, the first thing to do is to get a "token" from daybed.
This token is a way to identify yourself. A token contains two parts: a token
id (that you can publicly share) and a secret (that's very similar to
a password).

Here is how to get your credentials::

    http post http://0.0.0.0:8000/tokens

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


Now, you can use these credentials for the next requests.


Model management
----------------

First, we put a definition under the name "todo".


**PUT /models**

We want to push this to daybed, if we run it locally, that would be something
like this::

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

    http put http://localhost:8000/models/todo @definition --verbose --auth-type=hawk --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

And we get back::

    HTTP/1.1 200 OK
    Content-Length: 14
    Content-Type: application/json; charset=UTF-8
    Date: Thu, 24 Jul 2014 18:35:10 GMT
    Server: waitress

    {
        "id": "todo"
    }

Note that you could have done this call without being authenticated, by
authenticating, you and only you have the right to do some changes to this
model. You can change the permissions, we will see how to do so later on.

In case you don't want to define a name yourself for your model, you can do the
exact same call, replacing the http method from PUT to POST. don't provide a
name and daybed will generate one for you.

**GET /models**

We can now get our models back::

    http get http://localhost:8000/models/todo --verbose --auth-type=hawk --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

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

In case you are not authenticated, you couldn't see anything and would get a
401 answer from the server.


Pushing data
------------

**POST /models/{modelname}/records**
**PUT /models/{modelname}/records/{id}**

Now that we defined the schema, we want to push some real data there!::

    http POST http://localhost:8000/models/todo/records item="work on daybed" status="done"\
    --verbose --auth-type=hawk --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

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

And we get this in exchange, which is the id of the created document.

.. note::
    When you push some data, you can also send a special header, named
    `X-Daybed-Validate-Only`, which will allow you to only validate the
    resource you are sending, without actually recording it to the database.


**GET /models/{modelname}/records**

Using the GET method, you can get back the data you posted::

    http get http://localhost:8000/models/todo/records\
    --verbose --auth-type=hawk --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:' --json

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

    curl http://localhost:8000/models/todo/definition -u admin@example.com:apikey | python -m json.tool

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


Manipulating ACLs
-----------------

XXX Todo


Listing the supported fields
----------------------------

Daybed supports a bunch of fields. You can actually easily add some to your
instances. Sometimes, it can be useful to have a list of these fields. You can
hit the `/fields` endpoint for this purpose::

  http GET http://localhost:8000/fields --verbose --json
