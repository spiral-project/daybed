ACLs
####

In daybed, ACLs are implemented so you can chose who is able to have which
privileges on the content.

Each time a new model is created, a :term:`policy` is attached to it. A policy
associates roles to permissions. Here are exemples of what you can find in
a policy:

- "All the users have the right to push new content to this model"
- "Alexis is able to delete content from others"
- "The users in the group 'rangers' have the right to create new records".

Roles
=====

Some default :term:`roles` exist which can be reused when defining a model
policy.

*Roles* are defined by the model itself, but some default ones already exist:

- admins
- users
- authors

Users and groups
================

Each user can be associated to a number of groups. Groups start by `group:` in
the daybed storage layer.

Rights
======

Rights are defined for:

- the definition
- the users
- the policy
- the data
