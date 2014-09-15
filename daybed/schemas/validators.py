from __future__ import absolute_import
from functools import partial
from copy import deepcopy
import json
import datetime

import six
from colander import (
    SchemaNode, Mapping, Sequence, Length, String, null, Invalid, OneOf
)
from pyramid.security import Authenticated, Everyone

from daybed.backends.exceptions import ModelNotFound
from daybed.permissions import PERMISSIONS_SET
from daybed.backends.exceptions import CredentialsNotFound
from . import registry, TypeFieldNode, get_db


class DefinitionSchema(SchemaNode):
    def __init__(self, *args, **kwargs):
        super(DefinitionSchema, self).__init__(Mapping(), *args, **kwargs)
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
        self.add(DefinitionSchema(name='definition'))

    def deserialize(self, cstruct=null):
        self.children = self.children[:1]
        value = super(ModelSchema, self).deserialize(cstruct)

        definition = value['definition']
        self.add(SchemaNode(Sequence(), RecordSchema(definition),
                            name='records', missing=[]))

        return super(ModelSchema, self).deserialize(cstruct)


class IdentifierValidator(object):
    def __init__(self, db):
        self.db = db

    def __call__(self, node, value):
        if value not in (Authenticated, Everyone):
            try:
                self.db.get_token(value)
            except CredentialsNotFound:
                msg = u"Credentials id '%s' could not be found." % value
                raise Invalid(node, msg, value)


class PermissionValidator(OneOf):
    def __init__(self):
        valid = list(PERMISSIONS_SET) + ['all']
        super(PermissionValidator, self).__init__(valid)

    def __call__(self, node, value):
        strip_perm = value.lstrip('-').lstrip('+').lower()
        return super(PermissionValidator, self).__call__(node, strip_perm)


class PermissionsSchema(SchemaNode):
    def __init__(self, *args, **kwargs):
        super(PermissionsSchema, self).__init__(Mapping(unknown='preserve'),
                                                *args, **kwargs)

    def deserialize(self, cstruct=null):
        self.children = []
        permissions = super(PermissionsSchema, self).deserialize(cstruct)

        permissions = self._substitute_by_system(permissions)

        identifier_validator = IdentifierValidator(get_db())
        permission_node = SchemaNode(String(), validator=PermissionValidator())

        for identifier in permissions.keys():
            identifier_validator(self, identifier)
            self.add(SchemaNode(Sequence(),
                                permission_node,
                                name=identifier))
        return super(PermissionsSchema, self).deserialize(permissions)

    def _substitute_by_system(self, cstruct):
        for identifier in cstruct:
            if identifier in ("Authenticated", "Everyone"):
                saved = cstruct.pop(identifier)
                identifier = identifier.replace("Authenticated",
                                                Authenticated) \
                                       .replace("Everyone",
                                                Everyone)
                cstruct[identifier] = saved
        return cstruct


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
