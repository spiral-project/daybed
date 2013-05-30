import re
import datetime

from colander import (
    deferred,
    SchemaNode,
    Mapping,
    String,
    OneOf,
    Range,
    Sequence,
    Length,
    SchemaType,
    null,
    Int,
    Decimal,
    Boolean,
    Regex,
    Email,
    Date,
    DateTime
)


__all__ = ['registry', 'TypeField',
           'DefinitionValidator', 'SchemaValidator',
           'IntField', 'StringField', 'RangeField', 
           'RegexField', 'EmailField', 'URLField',
           'DecimalField', 'DateField', 'DateTimeField']


class AlreadyRegisteredError(Exception):
    pass


class NotRegisteredError(Exception):
    pass


class UnknownFieldTypeError(NotRegisteredError):
    """Raised if schema contains a field with an unknown type."""
    pass


class TypeRegistry(object):
    """Registry containing all the types.

    This can be extended by third parties, and is always imported from
    daybed.schemas.
    """

    def __init__(self):
        self._registry = {}

    def register(self, name, klass):
        if name in self._registry:
            raise AlreadyRegisteredError('The type %s is already registered' %
                                         name)
        self._registry[name] = klass

    def unregister(self, name):
        if name not in self._registry:
            raise NotRegisteredError('The model %s is not registered' % name)
        del self._registry[name]

    def validation(self, typename, **options):
        try:
            nodetype = self._registry[typename]
        except KeyError:
            raise UnknownFieldTypeError('Type "%s" is unknown' % typename)
        return nodetype.validation(**options)

    def definition(self, typename, **options):
        try:
            nodetype = self._registry[typename]
        except KeyError:
            raise UnknownFieldTypeError('Type "%s" is unknown' % typename)
        return nodetype.definition(**options)

    @property
    def names(self):
        return self._registry.keys()

    def add(self, name):
        """Class decorator, to register new types"""
        def decorated(cls):
            self.register(name, cls)
            return cls
        return decorated

registry = TypeRegistry()


class TypeField(object):
    node = String

    @classmethod
    def definition(cls):
        schema = SchemaNode(Mapping())
        schema.add(SchemaNode(String(), name='name'))
        schema.add(SchemaNode(String(), name='description'))
        schema.add(SchemaNode(String(), name='type',
                              validator=OneOf(registry.names)))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        keys = ['name', 'description', 'validator', 'missing']
        specified = [key for key in keys if key in kwargs.keys()]
        options = dict(zip(specified, [kwargs.get(k) for k in specified]))
        return SchemaNode(cls.node(), **options)


class TypeFieldNode(SchemaType):
    def deserialize(self, node, cstruct=null):
        try:
            schema = registry.definition(cstruct.get('type'))
        except UnknownFieldTypeError:
            schema = TypeField.definition()
        schema.deserialize(cstruct)


class DefinitionValidator(SchemaNode):
    def __init__(self):
        super(DefinitionValidator, self).__init__(Mapping())
        self.add(SchemaNode(String(), name='title'))
        self.add(SchemaNode(String(), name='description'))
        self.add(SchemaNode(Sequence(), SchemaNode(TypeFieldNode()),
                            name='fields', validator=Length(min=1)))


class SchemaValidator(SchemaNode):
    def __init__(self, definition):
        super(SchemaValidator, self).__init__(Mapping())
        for field in definition['fields']:
            fieldtype = field.pop('type')
            self.add(registry.validation(fieldtype, **field))


@registry.add('int')
class IntField(TypeField):
    node = Int


@registry.add('string')
class StringField(TypeField):
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
        # https://github.com/django/django/blob/273b96/django/core/validators.py#L45-L52
        urlpattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
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
        schema.add(SchemaNode(Boolean(), name='auto_now', missing=cls.auto_now))
        return schema

    @classmethod
    def validation(cls, **kwargs):
        auto_now = kwargs.get('auto_now', cls.auto_now)
        if auto_now:
            kwargs['missing'] = cls.default_value
        return super(AutoNowMixin, cls).validation(**kwargs).bind()


@registry.add('date')
class DateField(AutoNowMixin, TypeField):
    """A date field (ISO_8601, yyyy-mm-dd)."""
    node = Date

    @deferred
    def default_value(node, kw):
        return datetime.date.today()


@registry.add('datetime')
class DateTimeField(AutoNowMixin, TypeField):
    """A date time field (ISO_8601, yyyy-mm-ddTHH:MMZ)."""
    node = DateTime

    @deferred
    def default_value(node, kw):
        return datetime.datetime.now()
