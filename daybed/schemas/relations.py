import six
from pyramid.i18n import TranslationString as _
from colander import (String, SchemaNode, Invalid)

from daybed.backends.exceptions import ModelNotFound, RecordNotFound

from . import get_db
from .base import registry, TypeField, JSONList


class ModelExist(object):
    def __init__(self, db):
        self.db = db

    def __call__(self, node, value):
        try:
            self.db.get_model(value)
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
    hint = _('A choice among records')

    @classmethod
    def definition(cls, **kwargs):
        db = get_db()
        schema = super(OneOfField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(), name='model',
                   validator=ModelExist(db)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        db = get_db()
        kwargs['validator'] = RecordsExist(db, kwargs['model'])
        return super(OneOfField, cls).validation(**kwargs)


@registry.add('anyof')
class AnyOfField(TypeField):
    node = JSONList
    hint = _('Some choices among records')

    @classmethod
    def definition(cls, **kwargs):
        db = get_db()
        schema = super(AnyOfField, cls).definition(**kwargs)
        schema.add(SchemaNode(String(), name='model',
                   validator=ModelExist(db)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        db = get_db()
        kwargs['validator'] = RecordsExist(db, kwargs['model'])
        return super(AnyOfField, cls).validation(**kwargs)
