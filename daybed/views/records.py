import json

from cornice import Service
from pyramid.security import Everyone

from daybed.backends.exceptions import RecordNotFound, ModelNotFound
from daybed.schemas.validators import (RecordSchema, record_validator,
                                       validate_against_schema)


records = Service(name='records',
                  path='/models/{model_id}/records',
                  description='Collection of records')


record = Service(name='record',
                 path='/models/{model_id}/records/{record_id}',
                 description='Single record')


@records.get(permission='get_records')
@records.get(accept='application/vnd.geo+json', renderer='geojson',
             permission='get_records')
def get_records(request):
    """Retrieves all model records."""
    model_id = request.matchdict['model_id']
    try:
        request.db.get_model_definition(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {
            "error": "404 Not Found",
            "msg": "%s: model not found" % model_id
        }
    # Return array of records
    if "read_all_records" not in request.permissions:
        results = request.db.get_records(model_id, with_authors=True)
        results = [r['record'] for r in results
                   if set(request.principals).intersection(r['authors'])]
    else:
        results = request.db.get_records(model_id)
    return {'records': results}


@records.post(validators=record_validator, permission='post_record')
def post_record(request):
    """Saves a single model record.

    Posted record attributes will be matched against the related model
    definition.

    """
    # if we are asked only for validation, don't do anything more.
    if request.headers.get('X-Daybed-Validate-Only', 'false') == 'true':
        return

    model_id = request.matchdict['model_id']
    if request.token:
        token = request.token
    else:
        token = Everyone
    record_id = request.db.put_record(model_id, request.data_clean,
                                      [token])
    created = u'%s/models/%s/records/%s' % (request.application_url, model_id,
                                            record_id)
    request.response.status = "201 Created"
    request.response.headers['location'] = str(created)
    return {'id': record_id}


@records.delete(permission='delete_records')
def delete_records(request):
    """Deletes all records of model."""
    model_id = request.matchdict['model_id']
    try:
        request.db.delete_records(model_id)
    except ModelNotFound:
        request.response.status = "404 Not Found"
        return {
            "error": "404 Not Found",
            "msg": "%s: model not found" % model_id
        }
    return {"msg": "ok"}


@record.get(permission='get_record')
def get(request):
    """Retrieves a singe record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']
    try:
        return request.db.get_record(model_id, record_id)
    except RecordNotFound:
        request.response.status = "404 Not Found"
        return {
            "error": "404 Not Found",
            "msg": "%s: record not found %s" % (model_id, record_id)
        }


@record.put(validators=record_validator, permission='put_record')
def put(request):
    """Updates or creates a record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']

    if request.token:
        token = request.token
    else:
        token = Everyone

    record_id = request.db.put_record(model_id, request.data_clean,
                                      [token], record_id=record_id)
    return {'id': record_id}


@record.patch(permission='patch_record')
def patch(request):
    """Updates an existing record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']

    if request.token:
        token = request.token
    else:
        token = Everyone

    try:
        records = request.db.get_record(model_id, record_id)
    except RecordNotFound:
        request.response.status = "404 Not Found"
        return {
            "error": "404 Not Found",
            "msg": "%s: record not found %s" % (model_id, record_id)
        }

    records.update(json.loads(request.body.decode('utf-8')))
    definition = request.db.get_model_definition(model_id)
    validate_against_schema(request, RecordSchema(definition), records)
    if not request.errors:
        request.db.put_record(model_id, records, [token], record_id)
    return {'id': record_id}


@record.delete(permission='delete_record')
def delete(request):
    """Deletes a record."""
    model_id = request.matchdict['model_id']
    record_id = request.matchdict['record_id']

    try:
        deleted = request.db.delete_record(model_id, record_id)
    except RecordNotFound:
        request.response.status = "404 Not Found"
        return {
            "error": "404 Not Found",
            "msg": "%s: record not found %s" % (model_id, record_id)
        }
    return deleted
