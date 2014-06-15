import datetime

import colander

from daybed import schemas
from daybed.tests.support import unittest


class DefinitionTest(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.TypeField.definition()

    def test_field_type_is_required(self):
        self.assertRaises(colander.Invalid, self.schema.deserialize,
                          {'name': 'secret'})

    def test_field_type_must_be_known_from_registry(self):
        self.assertRaises(colander.Invalid, self.schema.deserialize,
                          {'name': 'a', 'type': 'b'})

    def test_field_name_can_contain_some_characters(self):
        good_names = ['a', 'B', 'a0', 'a_', 'a-b', 'Aa']
        for good_name in good_names:
            definition = self.schema.deserialize({'name': good_name,
                                                  'type': 'string'})
            self.assertEquals(definition['name'], good_name)

    def test_field_name_cannot_contain_bad_characters(self):
        bad_names = ['', '_', '-a', '0a', '_a', 'a b', 'a&a']
        for bad_name in bad_names:
            self.assertRaises(colander.Invalid, self.schema.deserialize,
                              {'name': bad_name, 'type': 'string'})

    def test_field_hint_takes_default_from_type_class(self):
        schema = schemas.StringField.definition()
        definition = schema.deserialize(
            {'name': 'no_hint',
             'type': 'string'})
        self.assertEquals(definition['hint'], schemas.StringField.hint)

    def test_field_hint_can_be_overriden(self):
        definition = self.schema.deserialize(
            {'name': 'secret',
             'type': 'string',
             'hint': 'A secret word'})
        self.assertEquals(definition['hint'], 'A secret word')

    def test_label_can_be_provided(self):
        definition = self.schema.deserialize(
            {'label': 'Some field',
             'name': 'address',
             'type': 'string'})
        self.assertEquals(definition.get('label'), 'Some field')

    def test_label_is_optional_and_empty_by_default(self):
        definition = self.schema.deserialize(
            {'name': 'firstname',
             'type': 'string'})
        self.assertEquals(definition['label'], '')

    def test_field_is_required_by_default(self):
        definition = self.schema.deserialize(
            {'name': 'firstname',
             'type': 'string'})
        self.assertEquals(definition['required'], True)

    def test_null_is_deserialized_if_field_is_not_required(self):
        definition = self.schema.deserialize(
            {'name': 'address',
             'type': 'int',
             'required': False})
        validator = schemas.TypeField.validation(**definition)
        self.assertEquals(colander.null, validator.deserialize(''))

    def test_deserialized_if_field_is_not_required_can_be_overridden(self):
        definition = self.schema.deserialize(
            {'name': 'address',
             'type': 'int',
             'required': False})
        before = schemas.TypeField.default_value
        schemas.TypeField.default_value = 0
        validator = schemas.TypeField.validation(**definition)
        self.assertEquals(0, validator.deserialize(''))
        schemas.TypeField.default_value = before


class BaseFieldsTests(unittest.TestCase):
    def test_int(self):
        schema = schemas.IntField.definition()
        definition = schema.deserialize(
            {'name': 'address',
             'type': 'int'})
        validator = schemas.IntField.validation(**definition)
        self.assertEquals(12, validator.deserialize('12'))
        self.assertRaises(colander.Invalid, validator.deserialize, '')
        self.assertRaises(colander.Invalid, validator.deserialize, 'abc')

    def test_enum(self):
        schema = schemas.EnumField.definition()
        definition = schema.deserialize(
            {'name': 'state',
             'type': 'enum',
             'choices': ['on', 'off']})

        validator = schemas.EnumField.validation(**definition)
        self.assertEquals('on', validator.deserialize('on'))
        self.assertRaises(colander.Invalid, validator.deserialize, '')
        self.assertRaises(colander.Invalid, validator.deserialize, 'ON')

    def test_choices(self):
        schema = schemas.ChoicesField.definition()
        definition = schema.deserialize(
            {'name': 'tags',
             'type': 'choices',
             'choices': ['a', 'b', 'c']})

        validator = schemas.ChoicesField.validation(**definition)
        self.assertEquals(['a'], validator.deserialize('a'))
        self.assertEquals(['a'], validator.deserialize(['a']))
        self.assertEquals(['a'], validator.deserialize('[a]'))
        self.assertEquals(['a'], validator.deserialize('["a"]'))
        self.assertEquals([u'a', u'b'], validator.deserialize('["a","b"]'))
        self.assertEquals(['a', 'b'], validator.deserialize('a,b'))
        self.assertEquals(['a', 'b', 'c'], validator.deserialize('[a,b,c]'))
        self.assertRaises(colander.Invalid, validator.deserialize, '')
        self.assertRaises(colander.Invalid, validator.deserialize, ['d'])
        self.assertRaises(colander.Invalid, validator.deserialize, '["a"')
        self.assertRaises(colander.Invalid, validator.deserialize, '[d]')
        self.assertRaises(colander.Invalid, validator.deserialize, '[a,d]')

    def test_range(self):
        schema = schemas.RangeField.definition()
        definition = schema.deserialize(
            {'name': 'age',
             'type': 'range',
             'min': 0, 'max': 100})

        validator = schemas.RangeField.validation(**definition)
        self.assertEquals(30, validator.deserialize(30))
        self.assertRaises(colander.Invalid, validator.deserialize, -5)
        self.assertRaises(colander.Invalid, validator.deserialize, 120)

    def test_regex(self):
        schema = schemas.RegexField.definition()
        definition = schema.deserialize(
            {'name': 'number',
             'type': 'regex',
             'regex': '\d+'})

        validator = schemas.RegexField.validation(**definition)
        self.assertEquals(1, int(validator.deserialize('1')))
        self.assertRaises(colander.Invalid, validator.deserialize, 'a')

    def test_email(self):
        schema = schemas.EmailField.definition()
        definition = schema.deserialize(
            {'name': 'address',
             'type': 'email'})

        validator = schemas.EmailField.validation(**definition)
        self.assertEquals('u@you.org', validator.deserialize('u@you.org'))
        self.assertEquals('u+i@you.org', validator.deserialize('u+i@you.org'))
        self.assertRaises(colander.Invalid, validator.deserialize,
                          'u i@you.org')

    def test_url(self):
        schema = schemas.URLField.definition()
        definition = schema.deserialize(
            {'name': 'homepage',
             'type': 'url'})

        validator = schemas.URLField.validation(**definition)
        self.assertEquals('http://daybed.lolnet.org',
                          validator.deserialize('http://daybed.lolnet.org'))
        self.assertRaises(colander.Invalid, validator.deserialize,
                          'http://lolnet/org')


class GroupFieldTests(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.GroupField.definition()
        self.definition = {
            'type': u'group',
            'fields': [{'type': u'int',
                        'name': u'a',
                        'hint': u'',
                        'label': u'',
                        'required': True}]}

    def test_a_group_has_no_name_nor_hint(self):
        definition = self.definition.copy()
        field = self.schema.deserialize(definition)
        definition['label'] = u''  # default empty
        self.assertDictEqual(definition, field)

    def test_a_group_can_have_label_and_description(self):
        definition = self.definition.copy()
        definition['label'] = u'Address'
        definition['description'] = u'A small text...'
        field = self.schema.deserialize(definition)
        self.assertDictEqual(definition, field)

    def test_a_group_must_have_at_least_one_field(self):
        definition = self.definition.copy()
        definition['fields'] = []
        self.assertRaises(colander.Invalid, self.schema.deserialize,
                          definition)

    def test_a_group_must_have_valid_fields(self):
        definition = self.definition.copy()
        definition['fields'].append({'type': u'int'})
        self.assertRaises(colander.Invalid, self.schema.deserialize,
                          definition)


class DateFieldTests(unittest.TestCase):
    def test_date(self):
        schema = schemas.DateField.definition()
        definition = schema.deserialize(
            {'label': 'First commit',
             'name': 'creation',
             'type': 'date'})

        validator = schemas.DateField.validation(**definition)
        self.assertEquals(datetime.date(2012, 4, 15),
                          validator.deserialize('2012-04-15'))
        self.assertRaises(colander.Invalid, validator.deserialize,
                          '2012/04/15')
        self.assertRaises(colander.Invalid, validator.deserialize,
                          '2012-13-01')
        self.assertRaises(colander.Invalid, validator.deserialize,
                          '2012-04-31')  # April has 30 days only
        self.assertEquals(validator.deserialize('2012-04-30T13:37Z'),
                          datetime.date(2012, 4, 30))

    def test_date_auto_today(self):
        schema = schemas.DateField.definition()
        definition = schema.deserialize(
            {'name': 'birth',
             'type': 'date',
             'autonow': True})
        validator = schemas.DateField.validation(**definition)
        defaulted = validator.deserialize(None)
        self.assertEqual(datetime.date.today(), defaulted)
        defaulted = validator.deserialize('')
        self.assertEqual(datetime.date.today(), defaulted)

    def test_datetime(self):
        schema = schemas.DateTimeField.definition()
        definition = schema.deserialize(
            {'label': 'First branch',
             'name': 'branch',
             'type': 'datetime'})

        validator = schemas.DateTimeField.validation(**definition)
        self.assertEquals(datetime.datetime(2012, 4, 16, 13, 45, 12, 0,
                                            colander.iso8601.UTC),
                          validator.deserialize('2012-04-16T13:45:12'))
        self.assertEquals(datetime.datetime(2012, 4, 16, 13, 45, 12, 0,
                                            colander.iso8601.UTC),
                          validator.deserialize('2012-04-16T13:45:12Z'))
        # Without time
        self.assertEquals(datetime.datetime(2012, 4, 16, 0, 0, 0, 0,
                                            colander.iso8601.UTC),
                          validator.deserialize('2012-04-16'))
        self.assertRaises(colander.Invalid, validator.deserialize,
                          '2012/04/16 13H45')
        self.assertRaises(colander.Invalid, validator.deserialize,
                          '2012-04-30T25:37Z')
        self.assertRaises(colander.Invalid, validator.deserialize,
                          '2012-04-30T13:60Z')

    def test_datetime_autonow(self):
        schema = schemas.DateTimeField.definition()
        definition = schema.deserialize(
            {'name': 'branch',
             'type': 'datetime',
             'autonow': True})
        validator = schemas.DateTimeField.validation(**definition)
        defaulted = validator.deserialize(None)
        self.assertTrue((datetime.datetime.now() - defaulted).seconds < 1)
        defaulted = validator.deserialize('')
        self.assertTrue((datetime.datetime.now() - defaulted).seconds < 1)

    def test_datetime_optional_autonow(self):
        schema = schemas.DateTimeField.definition()
        definition = schema.deserialize(
            {'name': 'branch',
             'type': 'datetime',
             'required': False})
        validator = schemas.DateTimeField.validation(**definition)
        self.assertEquals(colander.null, validator.deserialize(''))
        # If autonow, defaulted value should be now(), not null
        definition = schema.deserialize(
            {'name': 'branch',
             'type': 'datetime',
             'required': False,
             'autonow': True})
        validator = schemas.DateTimeField.validation(**definition)
        defaulted = validator.deserialize('')
        self.assertTrue((datetime.datetime.now() - defaulted).seconds < 1)


class JSONFieldTests(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.JSONField.definition()
        definition = self.schema.deserialize({'name': 'test',
                                              'type': 'json'})
        self.validator = schemas.JSONField.validation(**definition)

    def test_deserialization_works_with_empty_object(self):
        self.assertEquals(self.validator.deserialize('{}'), {})

    def test_deserialization_fails_if_json_is_invalid(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, '{yo:1}')

    def test_json_field_can_be_a_single_list(self):
        self.assertEquals(self.validator.deserialize('[1,"b",3]'),
                          [1, 'b', 3])

    def test_json_field_cannot_be_a_single_string(self):
        self.assertRaises(colander.Invalid,
                          self.validator.deserialize, 'cf spec')

    def test_json_field_is_idempotent(self):
        self.assertEquals(self.validator.deserialize([1, 'b', 3]),
                          [1, 'b', 3])
