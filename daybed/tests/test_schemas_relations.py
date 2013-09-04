import colander

from daybed import schemas
from daybed.tests.support import BaseWebTest


class RelationTest(BaseWebTest):
    def _create_definition(self, **kwargs):
        fakedef = {'description': 'stupid'}
        fakedef.update(**kwargs)
        return self.db.put_model_definition(fakedef, 'simple')

    def _create_data_item(self, **kwargs):
        fakedata = {'key': 'value'}
        fakedata.update(**kwargs)
        return self.db.put_data_item('simple', fakedata)

    def _create_model(self):
        self._create_definition()
        return self._create_data_item()


class OneOfFieldTest(RelationTest):
    def test_unknown_model(self):
        schema = schemas.OneOfField.definition()
        self.assertRaises(colander.Invalid,
                          schema.deserialize, {'name': 'foo',
                                               'type': 'oneof',
                                               'model': 'unknown'})

    def test_existing_model(self):
        self._create_model()
        schema = schemas.OneOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'oneof',
                                         'model': 'simple'})
        self.assertTrue(isinstance(definition, dict))

    def test_unknown_data_item(self):
        self._create_model()
        schema = schemas.OneOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'oneof',
                                         'model': 'simple'})
        validator = schemas.OneOfField.validation(**definition)
        self.assertRaises(colander.Invalid, validator.deserialize, 'unknown_id')

    def test_existing_data_item(self):
        data_id = self._create_model()
        schema = schemas.OneOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'oneof',
                                         'model': 'simple'})
        validator = schemas.OneOfField.validation(**definition)
        self.assertEqual(data_id, validator.deserialize(data_id))


class AnyOfFieldTest(RelationTest):
    def test_unknown_model(self):
        schema = schemas.AnyOfField.definition()
        self.assertRaises(colander.Invalid,
                          schema.deserialize, {'name': 'foo',
                                               'type': 'anyof',
                                               'model': 'unknown'})

    def test_existing_model(self):
        self._create_model()
        schema = schemas.AnyOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'anyof',
                                         'model': 'simple'})
        self.assertTrue(isinstance(definition, dict))

    def test_unknown_data_item(self):
        self._create_model()
        schema = schemas.AnyOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'anyof',
                                         'model': 'simple'})
        validator = schemas.AnyOfField.validation(**definition)
        self.assertRaises(colander.Invalid, validator.deserialize, 'unknown_id')

    def test_one_unknown_data_item(self):
        self._create_definition()
        known_id = self._create_data_item()
        schema = schemas.AnyOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'anyof',
                                         'model': 'simple'})
        validator = schemas.AnyOfField.validation(**definition)
        self.assertRaises(colander.Invalid, validator.deserialize, '["%s","unknown_id"]' % known_id)

    def test_existing_data_item(self):
        self._create_definition()
        known_id = self._create_data_item()
        known_id2 = self._create_data_item()
        schema = schemas.AnyOfField.definition()
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'anyof',
                                         'model': 'simple'})
        validator = schemas.AnyOfField.validation(**definition)
        self.assertEqual([known_id, known_id2], validator.deserialize("%s,%s" % (known_id, known_id2)))
        self.assertEqual([known_id, known_id2], validator.deserialize([known_id, known_id2]))
