import six
from pyramid.config import global_registries
from colander import (String, SchemaNode, Invalid)
from .base import registry, TypeField, JSONList


class ModelExist(object):
    def __init__(self, db):
        self.db = db

    def __call__(self, node, value):
        model = self.db.get_model_definition(value)
        if not model:
            msg = u"Model '%s' not found." % value
            raise Invalid(node, msg)


class DataItemsExist(object):
    def __init__(self, db, model_id):
        self.db = db
        self.model_id = model_id

    def __call__(self, node, value):
        if isinstance(value, six.string_types):
            value = [value]
        for record_id in value:
            record = self.db.get_data_item(self.model_id, record_id)
            if not record:
                msg = u"Record '%s' of model '%s' not found." % (record_id,
                                                                 self.model_id)
                raise Invalid(node, msg)


@registry.add('oneof')
class OneOfField(TypeField):
    node = String

    @classmethod
    def definition(cls, **kwargs):
        db = global_registries.last.backend._db
        schema = super(OneOfField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(), name='model',
                   validator=ModelExist(db)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        db = global_registries.last.backend._db
        kwargs['validator'] = DataItemsExist(db, kwargs['model'])
        return super(OneOfField, cls).validation(**kwargs)


@registry.add('anyof')
class AnyOfField(TypeField):
    node = JSONList

    @classmethod
    def definition(cls, **kwargs):
        db = global_registries.last.backend._db
        schema = super(AnyOfField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(), name='model',
                   validator=ModelExist(db)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        db = global_registries.last.backend._db
        kwargs['validator'] = DataItemsExist(db, kwargs['model'])
        return super(AnyOfField, cls).validation(**kwargs)
