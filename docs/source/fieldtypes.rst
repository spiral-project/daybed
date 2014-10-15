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


* **choices**: Some choices among values
    **Specific parameters:**
       * *choices*: An array of string items

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

It will accept a value that is greater or equal to min and less than equal to max.

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
       * *autonow*: Boolean, if true add the current date automatically. (default: false)

.. code-block:: json

    {
        "label": "Date of Birth",
        "name": "date",
        "type": "date",
        "autonow": true
    }


* **datetime**: A datetime in *yyyy-mm-ddTHH:MM:SS* format
    **Specific parameters:**
       * *autonow*: Boolean, if true add the current date automatically. (default: false)

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


* **metadata**: A model description field not used for validation
    No specific parameters.

.. code-block:: json

    {
        "label": "Title 1",
        "type": "metadata",
    }


   The metadata type is not really a field because the record has no trace of it.
   It can be use to add a description between fields.

   Has for the group type, it has no incidence on the definition, it
   can save information to display in between fields.

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
                  "label": "<strong>In a movie, you can find actors, please enter their names below.</strong>",
                  "type": "metadata"
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



* **json**: A JSON value
    No specific parameters.

    This can be used to store valid JSON, fields type are not validated.

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
    **Specific parameters:**
       * *model*: The name of the object
       * *fields*: A list of the object's fields.

Instead of the json type, you can choose to describe an object and validate it:

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
       * *item*: An object that defines the type of the list item
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

* **anyof**: Some choices among records of a given model
    **Specific parameters:**
       * *model*: The model id from which records can be selected

* **oneof**:
    **Specific parameters:**
       * *model*: The model id from which the record can be selected


Geometries
----------

* **geojson**: A GeoJSON geometry (not feature collection)
    No specific parameters.

* **point**: A point
    **Specific parameters:**
       * *gps*: A boolean that tells if the point coordinates are GPS coordinates and it will validate that coordinates are between -180,-90 and +180,+90 (Default: *true*)

* **line**: A line made of points
    **Specific parameters**
       * *gps*: A boolean that tells if the point coordinates are GPS coordinates and it will validate that coordinates are between -180,-90 and +180,+90  (Default: *true*)

* **polygon**: A polygon made of a closed line
    **Specific parameters**
       * *gps*: A boolean that tells if the point coordinates are GPS coordinates and it will validate that coordinates are between -180,-90 and +180,+90  (Default: *true*)
