import re
import json
import datetime

import six
from colander import (
    deferred,
    SchemaNode,
    String,
    OneOf,
    Range,
    Sequence,
    Length,
    List,
    ContainsOnly,
    null,
    Int,
    Decimal,
    Boolean,
    Regex,
    Email,
    Date,
    DateTime
)

from . import registry, TypeField


__all__ = ['IntField', 'StringField', 'RangeField',
           'RegexField', 'EmailField', 'URLField',
           'EnumField', 'ChoicesField', 'DecimalField',
           'DateField', 'DateTimeField']


@registry.add('int')
class IntField(TypeField):
    node = Int


@registry.add('string')
class StringField(TypeField):
    node = String


@registry.add('text')
class TextField(TypeField):
    node = String


@registry.add('decimal')
class DecimalField(TypeField):
    node = Decimal


@registry.add('boolean')
class BooleanField(TypeField):
    node = Boolean


@registry.add('enum')
class EnumField(TypeField):
    node = String

    @classmethod
    def definition(cls):
        schema = super(EnumField, cls).definition()
        schema.add(SchemaNode(Sequence(), SchemaNode(String()),
                              name='choices', validator=Length(min=1)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = OneOf(kwargs['choices'])
        return super(EnumField, cls).validation(**kwargs)


class JSONList(List):
    """Pure JSON or string, as serialized JSON or comma-separated values"""
    def deserialize(self, node, cstruct, **kwargs):
        if cstruct is null:
            return cstruct
        try:
            appstruct = cstruct
            if isinstance(cstruct, six.string_types):
                # Try JSON format
                appstruct = json.loads(cstruct)
        except ValueError:
            cstruct = re.sub(r'^\s*\[(.*)\]\s*', r'\1', cstruct)
            appstruct = re.split(r'\s*,\s*', cstruct)
        return super(JSONList, self).deserialize(node, appstruct, **kwargs)


@registry.add('choices')
class ChoicesField(TypeField):
    node = JSONList

    @classmethod
    def definition(cls):
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

    @classmethod
    def definition(cls):
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

    @classmethod
    def definition(cls):
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

    @classmethod
    def validation(cls, **kwargs):
        kwargs['validator'] = Email()
        return super(EmailField, cls).validation(**kwargs)


@registry.add('url')
class URLField(TypeField):
    """A URL field."""
    node = String

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
    """Mixin to share ``auto_now`` mechanism for both date and datetime fields.
    """
    auto_now = False

    @classmethod
    def definition(cls):
        schema = super(AutoNowMixin, cls).definition()
        schema.add(SchemaNode(Boolean(), name='auto_now',
                              missing=cls.auto_now))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        auto_now = kwargs.get('auto_now', cls.auto_now)
        if auto_now:
            kwargs['missing'] = cls.auto_value
        return super(AutoNowMixin, cls).validation(**kwargs).bind()


@registry.add('date')
class DateField(AutoNowMixin, TypeField):
    """A date field (ISO_8601, yyyy-mm-dd)."""
    node = Date

    @deferred
    def auto_value(node, kw):
        return datetime.date.today()


@registry.add('datetime')
class DateTimeField(AutoNowMixin, TypeField):
    """A date time field (ISO_8601, yyyy-mm-ddTHH:MMZ)."""
    node = DateTime

    @deferred
    def auto_value(node, kw):
        return datetime.datetime.now()
