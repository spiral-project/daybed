from pyramid.i18n import TranslationString as _
from colander import SchemaNode, drop

from . import TypeFieldNode
from .base import registry, TypeField, JSONList
from .json import JSONSequence


@registry.add('list')
class ListField(TypeField):
    hint = _('A list of values')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ListField, cls).definition(**kwargs)
        schema.add(SchemaNode(TypeFieldNode(named=False),
                   name='item',
                   missing=drop))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        """If ``item`` is specified in definition, the list is validated
        using a sequence of validation nodes.
        Otherwise as a list of any kind of values.
        """
        if 'item' in kwargs:
            item = kwargs.pop('item')
            nodetype = registry.validation(item['type'], **item)
            args = (JSONSequence(), nodetype)
        else:
            args = (JSONList(),)
        return super(ListField, cls).validation(*args, **kwargs)
