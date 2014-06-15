ACLs
####

In daybed, ACLs are implemented so you can chose who is able to have which
privileges on the content.

Each time a new model is created, a :term:`policy` is attached to it. A policy
associates roles to permissions. Here are exemples of what you can find in
a policy:

- "All the users have the right to push new content to this model"
- "Alexis is able to delete content from others"
- "Users of the group 'rangers' have the right to create new records".


Roles
=====

Some default :term:`roles` exist which can be reused when defining a model
policy.

*Roles* are defined by the model itself, but some default ones already exist:

- admins
- authors


Users and groups
================

Each user can be associated to a number of groups. Groups start by `group:` in
the daybed storage layer.

When you give a role to a group, all users inside the group have the role.

This can be really useful if a set of users share records or models
because you can add some of them by just adding them to a group
instead of adding them to the role of each records or models.

Let say, John and Mike manage the daybed server. They are in the owner
group. 

Later Mike leave the company and Dan arrive.

Because every model and records are own by the owner group John can
just remove Mike and add Dan inside the owner group to fix all the roles.


Policy and Rights
=================

The policy define rights for each roles of a model.

Rights are defined for:

- Definition
- Roles
- Policy
- Data

For example the read-only policy could be defined as this:

    Everybody can read anything but only Authenticated users can add
    new records and authors can update their records

In Daybed this will be something like:

.. code-block:: json

    {
        "role:admins": {"definition": {"create": true, "read": true,
                                       "update": true, "delete": true},
                        "records":    {"create": true, "read": true,
                                       "update": true, "delete": true},
                        "roles":      {"create": true, "read": true,
                                       "update": true, "delete": true},
                        "policy":     {"create": true, "read": true,
                                       "update": true, "delete": true}},
        "authors:": {"records": {"create": true, "read": true,
                                 "update": true, "delete": true}},
        "system.Authenticated": {"records":    {"create": true}
                                 "roles":      {"read": true},
                                 "policy":     {"read": true}},
        "system.Everyone": {"definition": {"read": true},
                            "records":    {"read": true}},
    }

When a user try an action, a list of principals is generated based on
the policy and the role the user has inside it.

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
        "policy_id": "read-only"
    }

If `john` tries to modify this record, he will have the following principals::

    ["system.Authenticated", "system.Everyone", "authors:"]

And the right set for all this principals will be accredited to him:

.. code-block:: json

    {
      "definition": {"read": true},
      "records":    {"create": true, "read": true,
                     "update": true, "delete": true},
      "roles":      {"read": true},
      "policy":     {"read": true}
    }

So John will be able to modify its record.

If Dan want to modify the same records he will get::

    ["system.Authenticated", "system.Everyone"]

.. code-block:: json

    {
      "definition": {"read": true},
      "records":    {"create": true, "read": true},
      "roles":      {"read": true},
      "policy":     {"read": true}
    }

He will not have the right to modify it.

Alexis is in the `admins` group, if he tries to modify the record, he
will get the `role:admins` and get full access::

    ["system.Authenticated", "system.Everyone", "role:admins"]

Alexis will be able to modify it.

If Mike tries to modify it, because he has the `role:admins` he will get full access::

    ["system.Authenticated", "system.Everyone", "role:admins"]

Mike will be able to modify it.
