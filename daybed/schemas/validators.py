from __future__ import absolute_import
from functools import partial
from copy import deepcopy
import json
import datetime

import six
from colander import (
    SchemaNode, Mapping, Sequence, Length, String, null, Invalid, drop
)
from pyramid.security import Authenticated, Everyone

from daybed.backends.exceptions import ModelNotFound
from daybed.permissions import PERMISSIONS_SET
from daybed.backends.exceptions import CredentialsNotFound
from . import registry, TypeFieldNode


class DefinitionSchema(SchemaNode):
    def __init__(self):
        super(DefinitionSchema, self).__init__(Mapping())
        self.add(SchemaNode(String(), name='title'))
        self.add(SchemaNode(String(), name='description'))
        self.add(SchemaNode(Sequence(), SchemaNode(TypeFieldNode()),
                            name='fields', validator=Length(min=1)))


class RecordSchema(SchemaNode):
    def __init__(self, definition):
        super(RecordSchema, self).__init__(Mapping())
        definition = deepcopy(definition)
        for field in definition['fields']:
            field['root'] = self
            fieldtype = field.pop('type')
            self.add(registry.validation(fieldtype, **field))


class ModelSchema(SchemaNode):
    def __init__(self):
        super(ModelSchema, self).__init__(Mapping())
        self.add(SchemaNode(DefinitionSchema(), name='definition'))

    def deserialize(self, cstruct=null):
        value = super(ModelSchema, self).deserialize(cstruct)

        definition = value['definition']
        self.add(SchemaNode(Sequence(), RecordSchema(definition),
                            name='records', missing=drop))

        return super(ModelSchema, self).deserialize(cstruct)


class IdentifierValidator(object):
    def __call__(self, node, value):
        if value not in (Authenticated, Everyone):
            try:
                self.db.get_token(value)
            except CredentialsNotFound:
                msg = u"Credential id '%s' not found." % value
                node.raise_invalid(msg)


class PermissionListSchema(SchemaNode):

    def __init__(self):
        super(PermissionListSchema, self).__init__(Sequence())

    def deserialize(self, cstruct=null):
        values = super(PermissionListSchema, self).deserialize(cstruct)

        lower_strip_dash = lambda perm: perm.lstrip('-').lstrip('+').lower()
        perms = set([lower_strip_dash(perm) for perm in values])

        if "all" in perms:
            perms = set(PERMISSIONS_SET)

        if not perms.issubset(PERMISSIONS_SET):
            unknown = perms - PERMISSIONS_SET
            msg = 'Invalid permissions: %s' % ', '.join(unknown)
            self.raise_invalid(msg)

        return perms


class PermissionsSchema(SchemaNode):
    def __init__(self):
        super(PermissionsSchema, self).__init__(Mapping())

    def deserialize(self, cstruct=null):
        value = super(PermissionsSchema, self).deserialize(cstruct)
        credentials_ids = value.keys()

        self.children = []
        for identifier in credentials_ids:
            if identifier in ("Authenticated", "Everyone"):
                identifier = identifier.replace("Authenticated",
                                                Authenticated) \
                                       .replace("Everyone",
                                                Everyone)
            IdentifierValidator()(self, identifier)

            self.add(PermissionListSchema(), name=identifier)

        return super(PermissionsSchema, self).deserialize(cstruct)


class RecordValidator(object):
    """A validator to check that a dictionnary matches the specified
    definition.
    """
    def __init__(self, definition):
        self.schema = RecordSchema(definition)

    def __call__(self, node, value):
        self.schema.deserialize(value)


def validate_against_schema(request, schema, data, field_name=None):
    try:
        data_pure = schema.deserialize(data)
        data_clean = post_serialize(data_pure)
        # Attach data_clean to request: see usage in views.
        request.data_clean = data_clean
    except Invalid as e:
        def output_error(error, recurse=False):
            # here we transform the errors we got from colander into cornice
            # errors
            for field, error in error.asdict().items():
                request.errors.add('body', field or field_name or '', error)
                if recurse:
                    map(output_error, e.children)
        output_error(e, True)


def post_serialize(data):
    """Returns the most agnostic version of specified data.
    (remove colander notions, datetimes in ISO, ...)
    """
    clean = dict()
    for k, v in data.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            clean[k] = v.isoformat()
        elif v is null:
            pass
        else:
            clean[k] = v
    return clean


def validator(request, schema):
    """Validates the request according to the given schema"""
    try:
        body = request.body.decode('utf-8')
        dictbody = json.loads(body) if body else {}
        validate_against_schema(request, schema, dictbody)
    except ValueError as e:
        request.errors.add('body', 'body', six.text_type(e))


definition_validator = partial(validator, schema=DefinitionSchema())
model_validator = partial(validator, schema=ModelSchema())
permissions_validator = partial(validator, schema=PermissionsSchema())


def record_validator(request):
    """Validates a request body according to its model definition.
    """
    model_id = request.matchdict['model_id']

    try:
        definition = request.db.get_model_definition(model_id)
        schema = RecordSchema(definition)
        validator(request, schema)
    except ModelNotFound:
        request.errors.add('path', 'modelname',
                           'Unknown model %s' % model_id)
        request.errors.status = 404
