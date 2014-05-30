from pyramid.i18n import TranslationString as _
from pyramid.config import global_registries
from colander import (Sequence, SchemaNode, Length, String, drop, Invalid)

from .base import registry, TypeField
from .relations import ModelExist


@registry.add('object')
class ObjectField(TypeField):
    hint = _('An object')

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
        schema.validator = validator

        return schema
