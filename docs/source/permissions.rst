Permissions
###########


In *Daybed*, permissions will let you define access rules on models, records
and even permissions.

They allow to express rules like :

- "Everyone can create new records on this model"
- "Alexis is able to delete records created by others"
- "Authenticated users can modify their own records"
- "Everyone can read the model definition"

This section describes how they work and how to use them.


Models permissions
==================

Here's a list of permissions you can define on a model:

- **read_definition**: read the model definition
- **read_acls**: read the model acls (who can do what)
- **update_definition**: update the model definition
- **update_acls**: change the ACLs on the models
- **delete_model**: delete a model
- **create_record**: add an entry to the model
- **read_all_records**: read all model's records
- **update_all_records**: update all model's records
- **delete_all_records**: delete any model's records
- **read_own_records**: read records on which you are an author
- **update_own_records**: update and change records on which you are an author
- **delete_own_records**: delete records on which you are an author


Global permissions
==================

There are three extra permissions that are configured at the server level:

- **create_model**: List of tokens allowed to create a model
- **create_token**: List of tokens allowed to create tokens
- **manage_tokens**: List of tokens allowed to delete tokens


Views permissions
=================

At the API level, you will often need more than one permissions to get
access to an API resource.

For example, if you want to get a model, you will need to have the
right for `read_definition` and `read_acls` as well as
`read_all_records` or `read_own_records`
