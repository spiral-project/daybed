.. _permissions-section:

Permissions
###########


In *Daybed*, permissions will let you define access rules on models, records
and even permissions.

They allow to express rules like:

- "Everyone can create new records on this model"
- "Alexis is able to delete records created by others"
- "Authenticated users can modify their own records"
- "Everyone can read the model definition"

This section describes how they work and how to use them.


Models permissions
==================

Here's a list of permissions you can define on a model:

- **read_definition**: read the model definition
- **read_permissions**: read the model permissions (who can do what)
- **update_definition**: update the model definition
- **update_permissions**: change the permissions for the model
- **delete_model**: delete the model
- **create_record**: add an entry to the model
- **read_all_records**: read all model's records
- **update_all_records**: update all model's records
- **delete_all_records**: delete any model's records
- **read_own_records**: read records on which you are an author
- **update_own_records**: update and change records on which you are an author
- **delete_own_records**: delete records on which you are an author


Views permissions
=================

At the API level, you will often need more than one permission to get
access to an API resource.

For example, if you want to get a complete model (definition and records),
you will need the following permissions:

- **read_definition** and **read_permissions**
- **read_all_records** or **read_own_records**


Global permissions
==================

There are three extra permissions that are configured at the server level:

- **create_model**: List of identifiers allowed to create a model
- **create_token**: List of identifiers allowed to create tokens
- **manage_tokens**: List of identifiers allowed to delete tokens

Those are configured via :ref:`a configuration file <custom-configuration>`,
with the following options:

- **create_model**: ``daybed.can_create_model`` (default: ``Everyone``)
- **create_token**: ``daybed.can_create_token`` (default: ``Everyone``)
- **manage_tokens**: ``daybed.can_manage_token`` (default: None)

Example::

    [app:main]
    daybed.can_create_model = Authenticated
    daybed.can_create_token = Everyone


Usage
=====

Permissions are set on models, as a *dictionnary* between :term:`identifiers` (*key id*)
and lists of :term:`permissions`.

In order to refer to anyone in the world, use the special *id* ``Everyone``
and to authenticated users with ``Authenticated``.

.. note::

    As explained in the :ref:`API usage section <usage-section>`, the
    *key ids* look like :term:`tokens`, but they are different : the *id*
    is the public part of your :term:`credentials`.
    The session token is private, since it contains the secret key.


When you create a model, you gain the full set of available permissions.

This means that the identifier you used in the request will be associated to all permissions::

    http GET http://localhost:8000/models/todo/permissions --verbose \
    --auth-type=hawk \
    --auth='ad37fc395b7ba83eb496849f6db022fbb316fa11081491b5f00dfae5b0b1cd22:'

    {
        "e0394574578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca": [
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
            "update_own_records",
            "update_permissions"
        ]
    }


Let's say you want to allow authenticated users to create records and manage
their own records on this model.

Permissions become::

    {
        "Authenticated": [
            "create_record",
            "read_own_records",
            "update_own_records",
            "delete_own_records"
        ],
        "e0394574578356252e2033b829b90291e2ff1f33ccbcbcec777485f3a5a10bca": [
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
            "update_own_records",
            "update_permissions"
        ]
    }

Modification
------------

You can use ``-`` and ``+`` to modify the existing set of permissions for an
identifier.

To grant ``create_record`` to anonymous users, ``read_permissions`` to
authenticated users and remove ``update_permissions`` from *id* ``220a1c..871``
you would have to send the following request::

    {
        "Everyone": ["+create_record"],
        "Authenticated": ["+read_permissions"],
        "220a1c..871": ["-update_permissions"]
    }

In order to add/remove all permissions to/from somebody, use the ``ALL`` shortcut::

    {
        "Authenticated": ["-ALL"],
        "220a1c..871": ["+ALL"]
    }

.. note::

    ``+`` is implicit, the permission is added if not specified
    (i.e. ``ALL`` is equivalent to ``+ALL``).


Concrete examples
=================

Collaborative editor (*pad*)
----------------------------

Everybody can read, create, modify and delete everyone's records.
However only the owner (*id* ``220a1c..871``) can modify the model definition and
adjust permissions.

::

    {
        "Everyone": [
            "read_definition",
            "create_record",
            "read_all_records",
            "update_all_records",
            "delete_all_records"
        ],
        "220a1c..871": [
            "ALL"
        ]
    }


If the *administrator* wants to share her privileges with others, she can either:

* share her :term:`token`
* create a new token, assign permissions to its *key id*, and share the new token

::

    {
        "Everyone": [
            "read_definition",
            "create_record",
            "read_all_records",
            "update_all_records",
            "delete_all_records"
        ],
        "6780dd..df1": [
            "update_definition",
            "read_permissions",
            "update_permissions"
        ],
        "220a1c..871": [
            "ALL"
        ]
    }


Online poll
-----------

Everybody can answer the poll, but are not allowed to correct their answers,
nor to see the poll results.

``read_definition`` is given to everyone, as it might be used to build the
form on the client-side::

    {
        "Everyone": [
            "read_definition",
            "create_record"
        ],
        "220a1c..871": [
            "ALL"
        ]
    }


TODO-list application
---------------------

The development team, who created the model, has the full set of permissions.

Everybody can manage their own records, but they are private.

::

    {
        "Everyone": [
            "read_definition",
            "create_record",
            "read_own_records",
            "update_own_records",
            "delete_own_records"
        ],
        "220a1c..871": [
            "ALL"
        ]
    }

.. note::

    Using *Everyone* instead of *Authenticated* will allow anonymous
    to manage a set of records that are shared among all anonymous users.

.. note::

    Users can share their todo list if they share their :term:`token`.
    But they cannot share it as read-only.

    In order to accomplish this, instead of having a unique model with
    everyone's records, each user will have to create their own model, on which
    they will gain the control of permissions.
