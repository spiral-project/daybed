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

The transcription of a basic types field can look like:

.. code-block:: json

    {
        "label": "The item",
        "name": "item",
        "hint": "Enter an Todo item",
        "required": true,
        "type": "string"
    }

You just have to select the right basic type.


Advanced types
--------------

* **enum**: A choice among values
    **Specific parameters:**
       * *choices*: An array of string items

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

* **range**: A number within limits
    **Specific parameters:**
       * *min*: An integer which is the minimum value of the field
       * *max*: An integer which is the maximum value of the field

* **regex**: A string matching a pattern
    **Specific parameters:**
       * *regexp*: The pattern the value should match to be valid.

* **date**: A date in *yyyy-mm-dd* format
    **Specific parameters:**
       * *autonow*: Boolean, if true add the current date automatically. (default: false)

* **datetime**: A datetime in *yyyy-mm-ddTHH:MM:SS* format
    **Specific parameters:**
       * *autonow*: Boolean, if true add the current date automatically. (default: false)

* **group**: A group of fields, can define fieldsets or multi-pages forms.
    **Specific parameters:**
       * *description*: A string to describe the group.
       * *fields*: A list of fields of the group.

* **metadata**: A model description field not used for validation
    No specific parameters.

* **json**: A JSON value
    No specific parameters.


Nested
------

* **object**: An object inside another model
    **Specific parameters:**
       * *model*: The name of the object
       * *fields*: A list of the object's fields.

* **list**: A list of objects inside another model
    **Specific parameters:**
       * *fields*: A list of the object's fields.


Relations
---------

* **anyof**: Some choices among records of a given models
    **Specific parameters:**
       * *model*: The model id from which records can be selected

* **oneof**:
    **Specific parameters:**
       * *model*: The model id from which the record can be selected


Geometries
----------

* **geojson**: A GeoJSON value
    No specific parameters.

* **point**: A point
    **Specific parameters:**
       * *gps*: A boolean that tells if the point coordinates are GPS coordinates (Default: *true*)

* **line**: A line made of points
    **Specific parameters**
       * *gps*: A boolean that tells if the point coordinates are GPS coordinates (Default: *true*)

* **polygon**: A polygon made of a closed line
    **Specific parameters**
       * *gps*: A boolean that tells if the point coordinates are GPS coordinates (Default: *true*)
