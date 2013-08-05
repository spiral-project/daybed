from pyramid.config import global_registries
from colander import (String, SchemaNode, Invalid)
from .base import registry, TypeField


class ModelExist(object):
    def __init__(self, db):
        self.db = db

    def __call__(self, node, value):
        model = self.db.get_model_definition(value)
        if not model:
            msg = u"Model '%s' not found." % value
            raise Invalid(node, msg)


class DataItemExist(object):
    def __init__(self, db, model_id):
        self.db = db
        self.model_id = model_id

    def __call__(self, node, value):
        record = self.db.get_data_item(self.model_id, value)
        if not record:
            msg = u"Record '%s' of model '%s' not found." % (value, self.model_id)
            raise Invalid(node, msg)


@registry.add('oneof')
class OneOfField(TypeField):
    node = String

    @classmethod
    def definition(cls, **kwargs):
        db = global_registries.last.backend.db()
        schema = super(OneOfField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(), name='model',
                   validator=ModelExist(db)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        db = global_registries.last.backend.db()
        kwargs['validator'] = DataItemExist(db, kwargs['model'])
        return super(OneOfField, cls).validation(**kwargs)
