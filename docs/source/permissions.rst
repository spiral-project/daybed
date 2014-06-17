Permissions
###########

In *Daybed*, permissions allow to control what are the privileges on
models, records, users ...and permissions !

They allow to express the following strategies :

- "Anyone can create new records on this model"
- "Alexis is able to delete records created by others"
- "Users of the group 'rangers' have the right to create new records"
- "Authenticated users can modify their own records"

This documentation describes how they work and how to use them.

Models permissions
==================

Permissions apply to the following actions :

* Create
* Read
* Update
* Delete

And cover the following aspects of a model :

* Its definition
* Its records
* The attached policy itself
* The roles given to users or groups for this model

For example, the following one allows manipulation
of records only :

==========  ======  ====  ======  ======  ============
            Create  Read  Update  Delete  *(Shortcut)*
==========  ======  ====  ======  ======  ============
definition          True                  -R--
records     True    True  True    True    CRUD
policy              True                  -R--
roles               True                  -R--
==========  ======  ====  ======  ======  ============


Users and groups
================

Users can be added to some groups.

If some permissions are given to a group, all its users inherit them.

This allows models and records administration by teams, from which you can add or
remove users.


Models roles and policy
=======================

Permissions on models are specified with a combination
of a :term:`policy` and some :term:`roles`.

Roles are defined on the model as a name and a list of users or groups.
Custom roles can be defined, but some are provided by default :

* ``role:admins``
* ``role:authors``

:notes:

    The creator of a **model** is put among the list of users for the ``admins`` role.

    The author of a **record** is put among the list of users for the ``authors`` role.


A policy is set on the model. It will assign permissions for each role.

When a user tries an action, a list of permissions is obtained based on the roles he
has on the model (or record) and the related policy.
He is denied if the permission required for his action is not among them.

:notes:

    When a user has several roles (e.g. authenticated and author), the permissions
    are summed.


Polices are re-usable as long as the roles names are identical.
Custom policies can be defined, but some are provided by default :

* ``anonymous``
* ``read-only``
* ``admin-only``

==============  ==========  ===========  ============  ============  ====================  ===============
Policy          Scope       role:admins  group:admins  role:authors  system.Authenticated  system.Everyone
==============  ==========  ===========  ============  ============  ====================  ===============
**anonymous**   definition                                                                 CRUD
|               records                                                                    CRUD
|               policy                                                                     CRUD
|               roles                                                                      CRUD
--------------  ----------  -----------  ------------  ------------  --------------------  ---------------
**read-only**   definition  CRUD                                                           -R--
|               records     CRUD                       --UD          C---                  -R--
|               policy      CRUD                                     -R--
|               roles       CRUD                                     -R--
--------------  ----------  -----------  ------------  ------------  --------------------  ---------------
**admin-only**  definition  CRUD         CRUD                                              -R--
|               records     CRUD         CRUD          CRUD
|               policy      CRUD         CRUD
|               roles       CRUD         CRUD
==============  ==========  ===========  ============  ============  ====================  ===============

The ``read-only`` can be explicited like this :

    Everybody can read anything but only authenticated users can create
    new records and only authors can update their records.


:notes:

    If not specified, the policy defined in the ``daybed.default_policy`` setting is attached
    to the model (``read-only`` by default).


Full example
============

Let say the user John try to edit the following record:

.. code-block:: json

    {
        'type': 'data',
        'authors': ['john'],
        'model_id': 'todo',
        'data': {"item": "finish the documentation", "status": "todo"}
    }

Of the following model:

.. code-block::

    {
        "type": "definition",
        "_id": "todo",
        "definition": {
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
        },
        "roles": {
            "admins": ["group:admins", "Mike"]
        },
        "policy": "read-only"
    }

If `john` tries to modify this record, *Daybed* will internally consider him with the following roles ::

    ["system.Authenticated", "system.Everyone", "role:authors"]

And the permissions set, obtained as the union of these from the policy ``read-only`` are :

==========  ========
            Obtained
==========  ========
definition  -R--
records     CRUD
policy      -R--
roles       -R--
==========  ========

Since he has update (U) for ``records``, John will be able to modify its record.

Now, if Dan wants to modify the same records he will be considered as ::

    ["system.Authenticated", "system.Everyone"]

And just obtain those permissions :

==========  ========
            Obtained
==========  ========
definition  -R--
records     CR--
policy      -R--
roles       -R--
==========  ========

Hence, he will not have the permission to modify it.

Alexis is in the `admins` group, which is given `admins` role on
this model. If he tries to modify the record, he will obtain full permissions.

If Mike tries to modify it, because is listed in the `admins` role on
this model, will get full permissions too.
