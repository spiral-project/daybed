from __future__ import absolute_import
from functools import partial
from copy import deepcopy
import json
import datetime

import six
from colander import (
    SchemaNode, Mapping, Sequence, Length, String, null, Invalid, OneOf, drop
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
        self.add(SchemaNode(Mapping(unknown="preserve"),
                            name="extra", missing=drop))
        self.add(SchemaNode(Sequence(), SchemaNode(TypeFieldNode()),
                            name='fields', validator=Length(min=1)))


class RecordSchema(SchemaNode):
    def __init__(self, definition):
        super(RecordSchema, self).__init__(Mapping())
        definition = deepcopy(definition)
        for field in definition['fields']:
            field['root'] = self
            fieldtype = field.pop('type')
            schema = registry.validation(fieldtype, **field)
            if schema:
                self.add(schema)


class ModelSchema(SchemaNode):
    """A model is a mapping with a mandatory ``definition``, and optionnal
    ``permissions`` or ``records`` (empty if not provided).
    """
    def __init__(self):
        super(ModelSchema, self).__init__(Mapping())
        # Child node for ``records`` will be added during deserialization
        self.add(DefinitionSchema(name='definition'))
        self.add(PermissionsSchema(name='permissions', missing={}))

    def deserialize(self, cstruct=null):
        # Remove potential extra child from previous deserialization
        self.children = self.children[:2]
        value = super(ModelSchema, self).deserialize(cstruct)

        # Add extra child ``records`` with validation based on definition
        definition = value['definition']
        self.add(SchemaNode(Sequence(), RecordSchema(definition),
                            name='records', missing=[]))

        return super(ModelSchema, self).deserialize(cstruct)


class IdentifierValidator(object):
    """A validator to check that the identifier exists in the database.
    """
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
    """A validator to check that the permission name is among those available.
    """
    def __init__(self):
        valid = list(PERMISSIONS_SET) + ['all']
        super(PermissionValidator, self).__init__(valid)

    def __call__(self, node, value):
        strip_perm = value.lstrip('-').lstrip('+').lower()
        return super(PermissionValidator, self).__call__(node, strip_perm)


class PermissionsSchema(SchemaNode):
    """Permissions are a mapping between :term:`identifiers` and lists of
    :term:`permissions`.
    We shall make sure that provided identifiers and permission names exist.
    """
    def __init__(self, *args, **kwargs):
        super(PermissionsSchema, self).__init__(Mapping(unknown='preserve'),
                                                *args, **kwargs)

    def deserialize(self, cstruct=null):
        # Remove potential extra children from previous deserialization
        self.children = []
        permissions = super(PermissionsSchema, self).deserialize(cstruct)

        identifier_validator = IdentifierValidator(get_db())

        def get_node_perms(identifier):
            identifier_validator(self, identifier)
            perm_node = SchemaNode(String(), validator=PermissionValidator())
            return SchemaNode(Sequence(), perm_node, name=identifier)

        # Add extra children nodes in mapping, based on provided identifiers
        permissions = self._substitute_by_system(permissions)
        for identifier in permissions.keys():
            self.add(get_node_perms(identifier))

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


def validate_against_schema(request, schema, data):
    """Validates and deliver colander exceptions as Cornice errors.
    """
    try:
        data_pure = schema.deserialize(data)
        data_clean = post_serialize(data_pure)
        # Attach data_clean to request: see usage in views.
        request.data_clean = data_clean
    except Invalid as e:
        # here we transform the errors we got from colander into cornice
        # errors
        for field, error in e.asdict().items():
            request.errors.add('body', field, error)


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
