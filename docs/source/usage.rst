=========================
How to use the daybed API
=========================

Daybed is a REST interface you can use to create definitions, edit them and
publish data that complies to these models.

Let's say we want to have a daybed managed todo list. First, we put
a definition under the name "todo".


Definition of the model
-----------------------

**PUT /model/**

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

    curl -XPUT http://localhost:8000/models/todo -d "${model}"

And we get back::

    "ok"

We can now get our models back::



Pushing data
------------

**POST /data/{modelname}**
**PUT /data/{modelname}/{id}**

Now that we defined the schema, we want to push some real data there::

    data='{"item": "finish the documentation", "status": "todo"}'
    curl -XPOST http://localhost:8000/data/todo -d "$data" -H "Content-Type: application/json"

And we get this in exchange, which is the id of the created document.::

    {"id": "37fa47f52ccdf1670747c39c85002cc6"}

.. note::
    When you push some data, you can also send a special header, named
    `X-Daybed-Validate-Only`, which will allow you to only validate the
    resource you are sending, without actually recording it to the database.

Getting data
------------

Of course, you can retrieve the data you pushed, as well as the definitions. To
do so, just issue some GET requests to the right resources.

Get back a definition
~~~~~~~~~~~~~~~~~~~~~

**GET /definition/{modelname}**

::

    curl http://localhost:8000/definitions/todo | python -m json.tool
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**GET /data/{modelname}**

::

    curl http://localhost:8000/todo
    {
    "data": [
        {
            "item": "finish the documentation", 
            "status": "todo"
        }, 
    ]
    }
