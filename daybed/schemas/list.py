from pyramid.i18n import TranslationString as _
from colander import (SchemaNode, String, drop, OneOf)

from .base import registry, TypeField, JSONList


@registry.add('list')
class ListField(TypeField):
    node = JSONList
    hint = _('A list of objects')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ListField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(),
                              name='itemtype',
                              validator=OneOf(registry.names),
                              missing=drop))
        return schema
