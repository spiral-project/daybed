Terminology
###########

*Daybed* concepts are very similar to those of any other storage or model validation
software.


.. glossary::
    :sorted:

    Model
        A model is made of a :term:`definition`, a set of :term:`records`, and
        a list of :term:`permissions`.

    Definition
        A schema defined as a list of fields, each one with a name, a type
        and potential parameters.

    Field
        A model definition is composed of multiple fields. Each one contains a
        name and a type.

    Field type
        A type, among those available, whose purpose is to validate values
        (e.g. ``int``, ``date``, ...).
        It may have mandatory or optional parameters, when used in a definition
        (e.g. ``choices``, ``regex``, ...).

    Records
    Record
        An item to be stored in a :term:`model`. It should provide a value for each required
        :term:`field` of the :term:`definition`.

    Permissions
    Permission
        An operation name, that allows access rules, to approve or deny requests on
        :term:`models`, :term:`records` or :term:`tokens`.
        Permissions are given to :term:`identifiers` as an associative array on
        models.

        For example, when trying to delete a record, if the request's *identifier* has not
        ``delete_records`` among its permission on this model, it will be
        denied.

        See :ref:`permissions section <permissions-section>`.

    Credentials
        Credentials are a way to authenticate yourself, and have two parts:

        1. an **id** -- :term:`identifier` that you can publicly share;
        2. a **key** -- similar to a password.

    Identifier
    Identifiers
        A unique *id*, part of the :term:`credentials`, that will be associated
        to the models and records you created.

        It is mentionned in :term:`permissions`.

    Token
    Tokens
        A *session token* (a.k.a ``Hawk-Session-Token``) is a string, which is unique for
        each pair of *id* and *key*, and helps you keep, handle or share your credentials
        as a simple string.
