Terminology
###########

*Daybed* concepts are very similar to those of any other storage or model validation
software.


.. glossary::
    :sorted:

    Model
        A model is made of a :term:`definition`, a set of :term:`records`.
        A list of custom :term:`roles` and a :term:`policy` (optional).

    Definition
        A schema defined as a list of fields, each one with a name, a type
        and potential parameters.

    Field
    Field type
        A type, among those available, whose purpose is to validate values
        (e.g. ``int``, ``date``, ...).
        It may have mandatory or optional parameters, when used in a definition
        (e.g. ``choices``, ``regex``, ...).

    Records
    Record
        An item to be stored in a :term:`model`. It should provide a value for each required
        :term:`field` of the :term:`definition`.

    Policy
        A reusable set of :term:`permissions` given to records authors, users in general
        or groups.

    Permissions
    Permission
        A boolean flag approving the ability to change the model :term:`definition`,
        as well as create, read, update or delete the model :term:`records`.

    Roles
        *Daybed* comes with the following built-in roles : *anonymous*, *authenticated*,
        *authors* and *admins*, that are assigned automatically.
        Additionnal roles can be defined with a name and a list of users and groups,
        at the :term:`model` level.

    User and groups
        Each user can be associated to a number of groups. When a user accesses a model,
        he receives a number of its :term:`roles`, depending of the groups he belongs to.
