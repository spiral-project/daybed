from daybed import TranslationString as _
from colander import SchemaNode, Sequence, drop

from . import TypeFieldNode
from .base import registry, TypeField, JSONList


class ItemsValid(object):
    def __init__(self, field):
        fieldtype = field['type']
        nodetype = registry.validation(fieldtype, **field)
        self.schema = SchemaNode(Sequence(), nodetype)

    def __call__(self, node, value):
        self.schema.deserialize(value)


@registry.add('list')
class ListField(TypeField):
    node = JSONList
    hint = _('A list of objects')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ListField, cls).definition(**kwargs)
        schema.add(SchemaNode(TypeFieldNode(named=False),
                   name='item',
                   missing=drop))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        if 'item' in kwargs:
            kwargs['validator'] = ItemsValid(kwargs['item'])
        return super(ListField, cls).validation(**kwargs)
