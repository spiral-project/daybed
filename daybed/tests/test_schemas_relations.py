import colander

from daybed import schemas
from daybed.tests.support import BaseWebTest


class FieldTypeTests(BaseWebTest):
    def _create_model(self):
        fakedef = {'description': 'stupid'}
        self.db.put_model_definition(fakedef, 'simple')
        fakedata = {'key': 'value'}
        return self.db.put_data_item('simple', fakedata)

    def test_unknown_model(self):
        schema = schemas.OneOfField.definition(db=self.db)
        self.assertRaises(colander.Invalid,
                          schema.deserialize, {'name': 'foo',
                                               'type': 'oneof',
                                               'model': 'unknown'})

    def test_existing_model(self):
        self._create_model()
        schema = schemas.OneOfField.definition(db=self.db)
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'oneof',
                                         'model': 'simple'})
        self.assertTrue(isinstance(definition, dict))

    def test_unknown_data_item(self):
        self._create_model()
        schema = schemas.OneOfField.definition(db=self.db)
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'oneof',
                                         'model': 'simple'})
        validator = schemas.OneOfField.validation(db=self.db, **definition)
        self.assertRaises(colander.Invalid, validator.deserialize, 'unknown_id')

    def test_existing_data_item(self):
        data_id = self._create_model()
        schema = schemas.OneOfField.definition(db=self.db)
        definition = schema.deserialize({'name': 'foo',
                                         'type': 'oneof',
                                         'model': 'simple'})
        validator = schemas.OneOfField.validation(db=self.db, **definition)
        self.assertEqual(data_id, validator.deserialize(data_id))
