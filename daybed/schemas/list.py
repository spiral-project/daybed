from pyramid.i18n import TranslationString as _
from colander import (Sequence, SchemaNode, Length, String, drop, OneOf,
                      Invalid)

from .base import registry, TypeField, JSONList


@registry.add('list')
class ListField(TypeField):
    node = JSONList
    hint = _('A list of objects')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ListField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(),
                              name='subtype',
                              validator=OneOf(registry.names),
                              missing=drop))
        schema.add(SchemaNode(Sequence(), TypeField.definition(),
                              name='subfields',
                              validator=Length(min=1),
                              missing=drop))

        def validator(node, value):
            if 'subtype' not in value and 'subfields' not in value:
                msg = u"No 'subtype' nor 'subfields'"
                raise Invalid(node, msg)
        schema.validator = validator

        return schema
