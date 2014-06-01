import six

from pyramid.i18n import TranslationString as _
from pyramid.config import global_registries
from colander import (Sequence, SchemaNode, Length, String, drop, Invalid)

from daybed.backends.exceptions import ModelNotFound

from .base import registry, TypeField
from .validators import RecordValidator
from .relations import ModelExist
from .json import JSONType


class ObjectMatchDefinition(object):
    """A validator to check that a dictionnary matches the specified
    definition.
    """
    def __init__(self, definition):
        self.schema = RecordValidator(definition)

    def __call__(self, node, value):
        self.schema.deserialize(value)


class ExclusiveKeys(object):
    """A dictionnary validator to check exclusive keys.
    It is valid if one and only one key is specified.
    """
    def __init__(self, *args):
        self.keys = args

    def __call__(self, node, value):
        provided_keys = six.iterkeys(value)
        match = set(self.keys).intersection(set(provided_keys))
        if len(match) > 1:
            msg = u"Choose between {0}".format(",".join(match))
            raise Invalid(node, msg)
        elif len(match) == 0:
            msg = u"Provide at least one of {0}".format(",".join(self.keys))
            raise Invalid(node, msg)


@registry.add('object')
class ObjectField(TypeField):
    hint = _('An object')
    node = JSONType

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ObjectField, cls).definition(**kwargs)

        db = global_registries.last.backend.db()
        schema.add(SchemaNode(String(),
                              name='model',
                              missing=drop,
                              validator=ModelExist(db)))

        schema.add(SchemaNode(Sequence(), TypeField.definition(),
                              name='fields',
                              validator=Length(min=1),
                              missing=drop))

        schema.validator = ExclusiveKeys('model', 'fields')
        return schema

    @classmethod
    def validation(cls, **kwargs):
        definition = cls._fetch_definition(kwargs)
        kwargs['validator'] = ObjectMatchDefinition(definition)
        return super(ObjectField, cls).validation(**kwargs)

    @classmethod
    def _fetch_definition(cls, field_definition):
        """Returns a model *definition* from the specified field definition,
        which provides either a list of fields or an existing model name.
        """
        if 'model' in field_definition:
            model = field_definition['model']
            db = global_registries.last.backend.db()
            try:
                definition = db.get_model_definition(model)
            except ModelNotFound:
                msg = u"Model '%s' not found." % model
                raise Invalid(msg)
        else:
            fields = [f.copy() for f in field_definition['fields']]
            definition = dict(fields=fields)

        return definition
