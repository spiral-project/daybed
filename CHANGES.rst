Changelog
=========

1.2 (unreleased)
----------------

- No changes yet.


1.1 (2014-11-12)
----------------

**Bug fixes**

- Fix storage of deserialized values for object and list field types.
- Make sure errors are send in JSON

**New features**

- Add new PUT end-point on ``/model/<id>/definition`` to update model definitions.
- Rewrite validators using schemas
- Support permissions in model put/post
- Improve documentation about fields
- Add a annotation field
- Accept extra property on models and records
- Add Koremutake ids generator
- Add Basic Auth on POST /tokens to always grab the same token
- Allow POST on the search endpoint


1.0.1 (2014-09-12)
----------------

- Allow CouchDB to run without being able to create the database.


1.0 (2014-09-12)
----------------

- Add permissions management
- Change API endpoints to clean the code and be more RESTful
- Implement PATCH on records
- Add authorization policies
- Add GeoJSON renderer
- Add GeoJSON field type
- Add JSON field type
- Add Multiple choices relation field
- Add multi backends tests
- Add BasicAuth and Person authentication

- Add Python 3 support
- Use tox to test on PyPy, Python 2.6, Python 2.7, Python 3.3 and flake8
- Add BSD Licence

- Deployed https://daybed.io/v1/


0.1 (2014-01-05)
----------------

- First proof of concept using CouchDB
- Anonymous data access
