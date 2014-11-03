.. _fieldtypes-section:

Daybed field types
==================

.. module:: daybed.schemas

Fields have these global properties:

* name
* label
* hint
* required
* type

You then have different kind of fields grouped in the following categories:

Basic types
-----------

Basic types don't have specific properties.

* **int**: An integer
* **string**: A set of characters
* **text**: A text
* **email**: A valid email
* **url**: A valid URL
* **decimal**: A decimal number
* **boolean**: A boolean

For example, when combining global properties and one of those basic field, it becomes:

.. code-block:: json

    {
        "label": "The item",
        "name": "item",
        "hint": "Enter an Todo item",
        "required": true,
        "type": "string"
    }

You just have to choose the right basic type.


Advanced types
--------------

* **enum**: A choice among values
    **Specific parameters:**
       * *choices*: An array of strings

.. code-block:: json

    {
        "label": "Task status",
        "name": "status",
        "type": "enum",
        "choices": [
            "done",
            "todo"
        ]
    }


* **choices**: Multiple choices among values
    **Specific parameters:**
       * *choices*: An array of strings

.. code-block:: json

    {
        "label": "Hobbies",
        "name": "hobbies",
        "type": "choices",
        "choices": [
            "Litterature",
            "Cinema",
            "Mountain Bike",
            "Motor Bike",
            "Sailing"
        ]
    }


* **range**: A number within limits
    **Specific parameters:**
       * *min*: An integer which is the minimum value of the field
       * *max*: An integer which is the maximum value of the field

It will accept a value that is greater than or equal to min and less than or
equal to max.

.. code-block:: json

    {
        "label": "Mountain bike Wheel Size (in mm)",
        "name": "wheel-size",
        "type": "range",
        "min": 239,
        "max": 622
    }


* **regex**: A string matching a pattern
    **Specific parameters:**
       * *regexp*: The pattern the value should match to be valid.

.. code-block:: json

    {
        "label": "French Mobile Phone Number",
        "name": "phone-number",
        "type": "regex",
        "regex": "^0[6-7][0-9]{8}$"
    }


* **date**: A date in *yyyy-mm-dd* format
    **Specific parameters:**
       * *autonow*: Boolean, add the current date automatically if true. (default: false)

.. code-block:: json

    {
        "label": "Date of Birth",
        "name": "date",
        "type": "date",
        "autonow": true
    }


* **datetime**: A datetime in *yyyy-mm-ddTHH:MM:SS* format
    **Specific parameters:**
       * *autonow*: Boolean, add the current datetime automatically if true. (default: false)

.. code-block:: json

    {
        "label": "Time of Birth",
        "name": "date_of_birth",
        "type": "datetime"
    }


* **group**: A group of fields, can define fieldsets or multi-pages forms.
    **Specific parameters:**
       * *description*: A string to describe the group.
       * *fields*: A list of fields of the group.

.. code-block:: json

    {
        "label": "Fieldset",
        "type": "group",
        "fields": [
            {
                "label": "Gender",
                "name": "gender",
                "type": "enum",
                "choices": [
                    "Mr",
                    "Miss",
                    "Ms"
                ]
            },
            {
                "label": "Firstname",
                "name": "firstname",
                "type": "string"
            },
            {
                "label": "Lastname",
                "name": "lastname",
                "type": "string"
            }
        ]
    }

Groups are ignored during validation, and records are posted like this:

.. code-block:: json

    {"gender": "Mr", "firstname": "Remy", "lastname": "Hubscher"}


* **annotation**: A model description field not used for validation
    No specific parameters.

.. code-block:: json

    {
        "label": "Title 1",
        "type": "annotation",
    }


The annotation type is not really a field because the record has no trace of it.
It can be used to add a description between fields.

Like the ``group`` field type, it can help to build the form layout.

For instance:

.. code-block:: json

    {"definition":
      {
        "title": "Movies",
        "description": "List of movies I like.",
        "fields": [
          {
              "label": "Movie",
              "name": "movie",
              "type": "object",
              "fields": [
                {
                  "label": "Title",
                  "name": "title",
                  "type": "string"
                },
                {
                  "label": "Director",
                  "name": "director",
                  "hint": "The Movie's director",
                  "type": "string"
                },
                {
                  "label": "In a movie, you can find actors, please enter their names below.",
                  "type": "annotation",
                  "css": "font-weigth: bold"
                },
                {
                  "label": "Actors",
                  "name": "actors",
                  "type": "list",
                  "item": {"type": "string", "hint": "Full name of the actors."}
                }
              ]
          }
        ]
      }
    }


The `css` property is just an example of how we could handle the
styling of the annotation here, but it could be anything else.


* **json**: A JSON value
    No specific parameters.

    Beyond formatting, the content is not validated

.. code-block:: json

    {
        "label": "JSON object",
        "name": "movie",
        "type": "json"
    }

Then you can use it like so:

.. code-block:: json

    {
      "movie": {
        "title": "The Island",
        "director": "Michael Bay",
        "actors": ["Scarlett Johnsson", "Erwan McGregor"],
        "year": 2005
      }
    }



Nested
------

* **object**: An object inside another model
    **Specific parameters**, used to validate the content. Only one of them should be specified.
         * *fields*: A list of fields like in a model definition.
         * *model*: The id of an existing model.

Unlike the ``json`` type, the content will be validated, using either the list
of fields or the definition of the specified model

.. code-block:: json

    {
      "label": "Movie",
      "name": "movie",
      "type": "object",
      "fields": [
        {
          "label": "Title",
          "name": "title",
          "type": "string"
        },
        {
          "label": "Director",
          "name": "director",
          "type": "string"
        },
        {
          "label": "Actors",
          "name": "actors",
          "type": "list",
          "item": {"type": "string"}
        }
      ]
    }


* **list**: A list of objects inside another model
    **Specific parameters:**
       * *item*: Defines the type of the list item
           * *type*: The type of the item
           * *hint*: The description of the item

.. code-block:: json

    {
      "label": "Movie",
      "name": "movie",
      "type": "list",
      "item": {
        "type": "object",
        "hint": "Description of a movie",
        "fields": [
          {
            "label": "Title",
            "name": "title",
            "type": "string"
          },
          {
            "label": "Director",
            "name": "director",
            "type": "string"
          }
        ]
      }
    }


Relations
---------

* **anyof**: Any number of choices among records of a given model
    **Specific parameters:**
       * *model*: The model id from which records can be selected

.. code-block:: json

    {
      "name": "actors",
      "type": "anyof",
      "model": "generic:people:moviestars",
      "label": "Movie actors"
    }

* **oneof**: One choice among records of a given model
    **Specific parameters:**
       * *model*: The model id from which the record can be selected

.. code-block:: json

    {
      "name": "maincharacter",
      "type": "oneof",
      "model": "generic:people:moviestars",
      "label": "Main character"
    }

Geometries
----------

* **geojson**: A `GeoJSON`_ geometry (not a FeatureCollection)
    No specific parameters.

.. _GeoJSON: http://geojson.org/

.. code-block:: json

    {
      "label": "where is it?",
      "name": "place",
      "type": "geojson"
    }

Then you can use it like so:

.. code-block:: json

    http POST http://localhost:8000/v1/models/todo/records \
    item="work on daybed" status="done" \
    place='{"type": "Point", "coordinates": [0.4, 45.0]}' \
    --verbose --auth-type=hawk \
    --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    {
      "item": "work on daybed",
      "place": {
        "coordinates": [
          0.4,
          45.0
        ],
        "type": "Point"
      },
      "status": "done"
    }



* **point**: A point
    **Specific parameters:**
       * *gps*: A boolean that tells if the point coordinates are GPS
         coordinates and it will validate that coordinates are between
         ``-180,-90`` and ``+180,+90`` (Default: *true*)

.. code-block:: json

    {
      "label": "where is it?",
      "name": "place",
      "type": "point"
    }

Then you can use it like so:

.. code-block:: json

    http POST http://localhost:8000/v1/models/todo/records \
    item="work on daybed" status="done" \
    place="[0.4, 45.0]" \
    --verbose --auth-type=hawk \
    --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    {
      "item": "work on daybed",
      "place": [
        0.4,
        45.0
      ],
      "status": "done"
    }


* **line**: A line made of points
    **Specific parameters**
       * *gps*: A boolean that tells if the point coordinates are GPS
         coordinates and it will validate that coordinates are between
         ``-180,-90`` and ``+180,+90`` (Default: *true*)

.. code-block:: json

    {
      "label": "where is it?",
      "name": "place",
      "type": "line"
    }

Then you can use it like so:

.. code-block:: json

    http POST http://localhost:8000/v1/models/todo/records \
    item="work on daybed" status="done" \
    place="[[0.4, 45.0], [0.6, 65.0]]" \
    --verbose --auth-type=hawk \
    --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    {
      "item": "work on daybed",
      "place": [
        [
          0.4,
          45.0
        ],
        [
          0.6,
          65.0
        ]
      ],
      "status": "done"
    }

* **polygon**: A polygon made of a closed line
    **Specific parameters**
       * *gps*: A boolean that tells if the point coordinates are GPS
         coordinates and it will validate that coordinates are between
         ``-180,-90`` and ``+180,+90`` (Default: *true*)

.. code-block:: json

    {
      "label": "where is it?",
      "name": "place",
      "type": "polygon"
    }

Then you can use it like so:

.. code-block:: json

    http POST http://localhost:8000/v1/models/todo/records \
    item="work on daybed" status="done" \
    place="[[[0.4, 45.0], [0.6, 65.0], [0.8, 85.0], [0.4, 45.0]]]" \
    --verbose --auth-type=hawk \
    --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    {
      "item": "work on daybed",
      "place": [
        [
          [
            0.4,
            45.0
          ],
          [
            0.6,
            65.0
          ],
          [
            0.8,
            85.0
          ],
          [
            0.4,
            45.0
          ]
        ]
      ],
      "status": "done"
    }
