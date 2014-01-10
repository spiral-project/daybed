import six
from pyramid.config import global_registries
from colander import (String, SchemaNode, Invalid)

from daybed.backends.exceptions import ModelNotFound, RecordNotFound
from .base import registry, TypeField, JSONList


class ModelExist(object):
    def __init__(self, db):
        self.db = db

    def __call__(self, node, value):
        try:
            self.db.get_model_definition(value)
        except ModelNotFound:
            msg = u"Model '%s' not found." % value
            raise Invalid(node, msg)


class RecordsExist(object):
    def __init__(self, db, model_id):
        self.db = db
        self.model_id = model_id

    def __call__(self, node, value):
        if isinstance(value, six.string_types):
            value = [value]
        for record_id in value:
            try:
                self.db.get_record(self.model_id, record_id)
            except RecordNotFound:
                msg = u"Record '%s' of model '%s' not found." % (record_id,
                                                                 self.model_id)
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
        kwargs['validator'] = RecordsExist(db, kwargs['model'])
        return super(OneOfField, cls).validation(**kwargs)


@registry.add('anyof')
class AnyOfField(TypeField):
    node = JSONList

    @classmethod
    def definition(cls, **kwargs):
        db = global_registries.last.backend.db()
        schema = super(AnyOfField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(), name='model',
                   validator=ModelExist(db)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        db = global_registries.last.backend.db()
        kwargs['validator'] = RecordsExist(db, kwargs['model'])
        return super(AnyOfField, cls).validation(**kwargs)
