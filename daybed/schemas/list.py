from pyramid.i18n import TranslationString as _
from colander import (SchemaNode, String, Sequence, drop, OneOf,
                      Invalid, Mapping)

from .base import registry, TypeField, JSONList


class ParametersMatchItemType(object):
    def __call__(self, node, value):
        if 'parameters' in value and 'itemtype' not in value:
            msg = u'Missing itemtype since parameters is provided'
            raise Invalid(node, msg)
        if 'itemtype' in value and 'parameters' in value:
            itemtype = value['itemtype']
            parameters = value['parameters']
            schema = registry.definition(itemtype)

            # Instanciate a fake type to check parameters match what's accepted
            # by this field type.
            parameters.update(name='fake', type=itemtype)
            schema.deserialize(parameters)


class ItemsValid(object):
    def __init__(self, fieldtype, **options):
        nodetype = registry.validation(fieldtype, **options)
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
        schema.add(SchemaNode(String(),
                              name='itemtype',
                              validator=OneOf(registry.names),
                              missing=drop))
        schema.add(SchemaNode(Mapping(unknown='preserve'),
                              name='parameters',
                              missing=drop))
        schema.validator = ParametersMatchItemType()
        return schema

    @classmethod
    def validation(cls, **kwargs):
        if 'itemtype' in kwargs:
            itemparameters = kwargs.get('parameters', {})
            kwargs['validator'] = ItemsValid(kwargs['itemtype'],
                                             **itemparameters)
        return super(ListField, cls).validation(**kwargs)
