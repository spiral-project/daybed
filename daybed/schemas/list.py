from pyramid.i18n import TranslationString as _
from colander import (Sequence, SchemaNode, Length)

from .base import registry, TypeField, JSONList


@registry.add('list')
class ListField(TypeField):
    node = JSONList
    hint = _('A list of objects')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ListField, cls).definition(**kwargs)
        schema.add(SchemaNode(Sequence(), TypeField.definition(),
                              name='subtype', validator=Length(min=1)))
        return schema
