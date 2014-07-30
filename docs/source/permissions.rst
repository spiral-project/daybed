ACLs — Permissions
##################

In *Daybed*, permissions allow to control what are the privileges on
models, records and acls !

They allow to express the following strategies :

- "Everyone can create new records on this model"
- "Alexis is able to delete records created by others"
- "Authenticated users can modify their own records"
- "Everyone can read the model definition"

This documentation describes how they work and how to use them.


Models permissions
==================

There is a list of 12 permissions that you can add to a token on a
model.

- **read_definition**: You can read the model definition
- **read_acls**: You can read the model acls (who can do what)
- **update_definition**: You can update the model definition
- **update_acls**: You can change the ACLs on the models
- **delete_model**: You can delete a model
- **create_record**: You can add an entry to the model
- **read_all_records**: You can read all model's records
- **update_all_records**: You can update all model's records
- **delete_all_records**: You can delete any model's records
- **read_own_records**: You can read records on which you are an author
- **update_own_records**: You can update and change records on which you are an author
- **delete_own_records**: You can delete records on which you are an author

These are permissions that you can set on a model.


Global permissions
==================

There is three more permissions that are configured at the server level:

- **create_model**: List of people that have the right to create a model
- **create_token**: List of people that can create tokens
- **manage_tokens**: List of people that have the right to delete tokens


Views permissions
=================

At the API level, you will often need more than one permissions to get
access to a page.

For example, if you want to get a model you will need to have the
right for `read_definition` and `read_acls` as well as
`read_all_records` or `read_own_records`
