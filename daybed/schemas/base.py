import re
import datetime

from pyramid.i18n import TranslationString as _
from colander import (
    deferred,
    SchemaNode,
    String,
    OneOf,
    Range,
    Sequence,
    Length,
    ContainsOnly,
    Int,
    Decimal,
    Boolean,
    Regex,
    Email,
    Date,
    DateTime,
    Mapping,
    drop,
)

from . import registry, TypeField, TypeFieldNode
from .json import JSONList


__all__ = ['IntField', 'StringField', 'RangeField',
           'RegexField', 'EmailField', 'URLField',
           'EnumField', 'ChoicesField', 'DecimalField',
           'DateField', 'DateTimeField', 'GroupField',
           'AnnotationField']


@registry.add('int')
class IntField(TypeField):
    node = Int
    hint = _('An integer')


@registry.add('string')
class StringField(TypeField):
    node = String
    hint = _('A set of characters')


@registry.add('text')
class TextField(TypeField):
    node = String
    hint = _('A text')


@registry.add('annotation')
class AnnotationField(TypeField):
    required = False

    @classmethod
    def definition(cls, **kwargs):
        schema = SchemaNode(Mapping(unknown="preserve"))

        schema.add(SchemaNode(String(), name='label', missing=u''))
        schema.add(SchemaNode(String(), name='type',
                              validator=OneOf(["annotation"])))
        return schema


@registry.add('decimal')
class DecimalField(TypeField):
    node = Decimal
    hint = _('A decimal number')


@registry.add('boolean')
class BooleanField(TypeField):
    node = Boolean
    hint = _('True or false')


@registry.add('enum')
class EnumField(TypeField):
    node = String
    hint = _('A choice among values')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(EnumField, cls).definition()
        schema.add(SchemaNode(Sequence(), SchemaNode(String()),
                              name='choices', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = OneOf(kwargs['choices'])
        return super(EnumField, cls).validation(**kwargs)


@registry.add('choices')
class ChoicesField(TypeField):
    node = JSONList
    hint = _('Some choices among values')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(ChoicesField, cls).definition()
        schema.add(SchemaNode(Sequence(), SchemaNode(String()),
                              name='choices', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = ContainsOnly(kwargs['choices'])
        return super(ChoicesField, cls).validation(**kwargs)


@registry.add('range')
class RangeField(TypeField):
    node = Int
    hint = _('A number with limits')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(RangeField, cls).definition()
        schema.add(SchemaNode(Int(), name='min'))
        schema.add(SchemaNode(Int(), name='max'))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Range(min=kwargs.get('min'),
                                    max=kwargs.get('max'))
        return super(RangeField, cls).validation(**kwargs)


@registry.add('regex')
class RegexField(TypeField):
    """Allows to validate a field with a python regular expression."""
    node = String
    hint = _('A string matching a pattern')

    @classmethod
    def definition(cls, **kwargs):
        schema = super(RegexField, cls).definition()
        schema.add(SchemaNode(String(), name='regex', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Regex(kwargs['regex'])
        return super(RegexField, cls).validation(**kwargs)


@registry.add('email')
class EmailField(TypeField):
    """An email address field."""
    node = String
    hint = _('A valid email')

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Email()
        return super(EmailField, cls).validation(**kwargs)


@registry.add('url')
class URLField(TypeField):
    """A URL field."""
    node = String
    hint = _('A valid URL')

    @classmethod
    def validation(cls, **kwargs):
        # This one comes from Django
        # https://github.com/django/django/blob/273b96/
        # django/core/validators.py#L45-L52
        urlpattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        kwargs['validator'] = Regex(urlpattern, msg="Invalid URL")
        return super(URLField, cls).validation(**kwargs)


class AutoNowMixin(object):
    """Mixin to share ``autonow`` mechanism for both date and datetime fields.
    """
    autonow = False

    @classmethod
    def definition(cls, **kwargs):
        schema = super(AutoNowMixin, cls).definition()
        schema.add(SchemaNode(Boolean(), name='autonow',
                              missing=cls.autonow))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        autonow = kwargs.get('autonow', cls.autonow)
        if autonow:
            kwargs['missing'] = cls.auto_value
        return super(AutoNowMixin, cls).validation(**kwargs).bind()


@registry.add('date')
class DateField(AutoNowMixin, TypeField):
    """A date field (ISO_8601, yyyy-mm-dd)."""
    node = Date
    hint = _('A date (yyyy-mm-dd)')

    @deferred
    def auto_value(node, kw):
        return datetime.date.today()


@registry.add('datetime')
class DateTimeField(AutoNowMixin, TypeField):
    """A date time field (ISO_8601, yyyy-mm-ddTHH:MMZ)."""
    node = DateTime
    hint = _('A date with time (yyyy-mm-ddTHH:MM)')

    @deferred
    def auto_value(node, kw):
        return datetime.datetime.now()


@registry.add('group')
class GroupField(TypeField):
    @classmethod
    def definition(cls, **kwargs):
        schema = super(GroupField, cls).definition(**kwargs)
        # Keep the ``type`` node only
        schema.children = [c for c in schema.children
                           if c.name not in ('hint', 'name', 'required')]
        schema.add(SchemaNode(String(), name='description', missing=drop))
        schema.add(SchemaNode(Sequence(), SchemaNode(TypeFieldNode()),
                              name='fields', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        rootnode = kwargs.pop('root')
        # Add the group fields to the model definition node
        for field in kwargs['fields']:
            field['root'] = rootnode
            fieldtype = field.pop('type')
            rootnode.add(registry.validation(fieldtype, **field))
        # Ignore the group validation itself
        return SchemaNode(String(), missing=drop)
