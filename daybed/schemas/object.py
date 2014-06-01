from pyramid.i18n import TranslationString as _
from pyramid.config import global_registries
from colander import (Sequence, SchemaNode, Length, String, drop, Invalid)

from daybed.backends.exceptions import ModelNotFound

from .base import registry, TypeField
from .validators import RecordValidator
from .relations import ModelExist
from .json import JSONType


class RecordsValid(object):
    def __init__(self, definition):
        self.definition = definition
        self.schema = RecordValidator(definition)

    def __call__(self, node, value):
        self.schema.deserialize(value)


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

        def validator(node, value):
            if 'model' in value and 'fields' in value:
                msg = u"Cannot have both 'model' and 'fields'"
                raise Invalid(node, msg)
            if 'model' not in value and 'fields' not in value:
                msg = u"Must have at least 'model' or 'fields'"
                raise Invalid(node, msg)
        schema.validator = validator

        return schema

    @classmethod
    def validation(cls, **kwargs):
        if 'model' in kwargs:
            model = kwargs['model']
            db = global_registries.last.backend.db()
            try:
                definition = db.get_model_definition(model)
            except ModelNotFound:
                msg = u"Model '%s' not found." % model
                raise Invalid(msg)
        else:
            fields = [f.copy() for f in kwargs['fields']]
            definition = dict(fields=fields)

        kwargs['validator'] = RecordsValid(definition)

        return super(ObjectField, cls).validation(**kwargs)
