import mock

from daybed.schemas import registry

from .support import BaseWebTest
from .test_views import MODEL_DEFINITION, MODEL_RECORD


class ModelsIndicesTest(BaseWebTest):

    @mock.patch('elasticsearch.client.indices.IndicesClient.create')
    def test_index_created_on_model_post(self, create_index_mock):
        for i in range(3):
            self.app.post_json('/models', MODEL_DEFINITION,
                               headers=self.headers)
        self.assertEqual(create_index_mock.call_count, 3)

    @mock.patch('elasticsearch.client.indices.IndicesClient.create')
    def test_index_created_on_model_put(self, create_index_mock):
        for i in range(3):
            self.app.put_json('/models/test-%s' % i, MODEL_DEFINITION,
                              headers=self.headers)
        self.assertEqual(create_index_mock.call_count, 3)

    @mock.patch('elasticsearch.client.indices.IndicesClient.put_mapping')
    def test_mapping_is_created_on_model_creation(self, put_mapping_mock):
        for i in range(3):
            self.app.post_json('/models', MODEL_DEFINITION,
                               headers=self.headers)
        self.assertEqual(put_mapping_mock.call_count, 3)

    @mock.patch('elasticsearch.client.indices.IndicesClient.put_mapping')
    def test_mapping_is_created_on_model_put(self, put_mapping_mock):
        for i in range(3):
            self.app.put_json('/models/test-%s' % i, MODEL_DEFINITION,
                              headers=self.headers)
        self.assertEqual(put_mapping_mock.call_count, 3)

    @mock.patch('elasticsearch.client.indices.IndicesClient.delete')
    def test_existing_index_is_not_deleted_on_model_put(self, delete_mock):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.assertEqual(delete_mock.call_count, 0)

    @mock.patch('elasticsearch.client.indices.IndicesClient.delete_mapping')
    def test_existing_mapping_is_deleted_on_put(self, delete_mapping_mock):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.assertEqual(delete_mapping_mock.call_count, 1)

    @mock.patch('elasticsearch.client.indices.IndicesClient.delete')
    def test_index_deleted_on_model_deletion(self, delete_index_mock):
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.delete('/models/test',
                        headers=self.headers)
        delete_index_mock.assert_called_with(index='test')


class RecordsIndicesTest(BaseWebTest):

    def setUp(self):
        super(RecordsIndicesTest, self).setUp()
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_record_indexed_on_post(self, index_mock):
        for i in range(3):
            self.app.post_json('/models/test/records', MODEL_RECORD,
                               headers=self.headers)
        self.assertEqual(index_mock.call_count, 3)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_record_indexed_on_put(self, index_mock):
        self.app.put_json('/models/test/records/1', MODEL_RECORD,
                          headers=self.headers)
        self.assertEqual(index_mock.call_count, 1)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_existing_record_reindexed_on_put(self, index_mock):
        self.app.put_json('/models/test/records/1', MODEL_RECORD,
                          headers=self.headers)
        self.app.put_json('/models/test/records/1', MODEL_RECORD,
                          headers=self.headers)
        self.assertEqual(index_mock.call_count, 2)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_existing_record_reindexed_on_patch(self, index_mock):
        self.app.put_json('/models/test/records/1', MODEL_RECORD,
                          headers=self.headers)
        self.app.patch_json('/models/test/records/1', MODEL_RECORD,
                            headers=self.headers)
        self.assertEqual(index_mock.call_count, 2)

    @mock.patch('elasticsearch.client.Elasticsearch.delete')
    def test_record_unindexed_on_delete(self, delete_mock):
        self.app.put_json('/models/test/records/1', MODEL_RECORD,
                          headers=self.headers)
        self.app.delete('/models/test/records/1',
                        headers=self.headers)
        delete_mock.assert_called_with(index='test', doc_type='test',
                                       id='1', refresh=True)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_record_indexed_on_model_post(self, index_mock):
        definition = MODEL_DEFINITION.copy()
        for i in range(3):
            definition.setdefault('records', []).append(MODEL_RECORD)
        self.app.post_json('/models', definition,
                           headers=self.headers)
        self.assertEqual(index_mock.call_count, 3)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_record_indexed_on_model_put(self, index_mock):
        definition = MODEL_DEFINITION.copy()
        for i in range(3):
            definition.setdefault('records', []).append(MODEL_RECORD)
        self.app.put_json('/models/test', definition,
                          headers=self.headers)
        self.assertEqual(index_mock.call_count, 3)

    @mock.patch('elasticsearch.client.Elasticsearch.index')
    def test_existing_records_unindexed_on_model_put(self, delete_mock):
        no_records = MODEL_DEFINITION.copy()
        with_records = MODEL_DEFINITION.copy()
        for i in range(3):
            with_records.setdefault('records', []).append(MODEL_RECORD)
        self.app.put_json('/models/test', with_records,
                          headers=self.headers)
        self.app.put_json('/models/test', no_records,
                          headers=self.headers)
        self.assertEqual(delete_mock.call_count, 3)


ALL_FIELDS_DEFINITION = {
    'definition': {
        'title': 'all fields',
        'description': 'One optional field',
        'fields': [
            {'name': 'a', 'type': 'int'},
            {'name': 'b', 'type': 'boolean'},
            {'name': 'c', 'type': 'decimal'},
            {'name': 'd', 'type': 'string'},
            {'name': 'e', 'type': 'text'},
            {'name': 'f', 'type': 'url'},
            {'name': 'g', 'type': 'date'},
            {'name': 'h', 'type': 'datetime'},
            {'type': 'group', 'fields': [
                {'name': 'i', 'type': 'int'}
            ]},
            {'name': 'j', 'type': 'email'},
            {'name': 'k', 'type': 'json'},
            {'name': 'l', 'type': 'range', 'min': 10, 'max': 100},
            {'name': 'm', 'type': 'choices', 'choices': ['a']},
            {'name': 'n', 'type': 'enum', 'choices': ['a']},
            {'name': 'o', 'type': 'regex', 'regex': '.+'},
            {'name': 'p', 'type': 'list', 'itemtype': 'object',
                'parameters': {
                    'fields': [
                        {'name': 'pp', 'type': 'int'}
                    ]
                }},
            {'name': 'q', 'type': 'object', 'fields': [
                {'name': 'qq', 'type': 'int'}
            ]},
            {'name': 'r', 'type': 'geojson'},
            {'name': 's', 'type': 'line'},
            {'name': 't', 'type': 'point'},
            {'name': 'u', 'type': 'polygon'},
            {'name': 'v', 'type': 'anyof', 'model': 'simple'},
            {'name': 'w', 'type': 'oneof', 'model': 'simple'},
        ]
    }
}


class DefinitionMappingTest(BaseWebTest):

    def setUp(self):
        super(DefinitionMappingTest, self).setUp()

        self.app.put_json('/models/simple', MODEL_DEFINITION,
                          headers=self.headers)

        self.model = ALL_FIELDS_DEFINITION.copy()
        self.mapping = None
        mapping_mock = 'elasticsearch.client.indices.IndicesClient.put_mapping'
        with mock.patch(mapping_mock) as mocked:
            self.app.put_json('/models/test', self.model,
                              headers=self.headers)
            mapping_call = mocked.call_args_list[0]
            self.mapping = mapping_call[1]['body']

    def assertFieldMapping(self, fields, mapping):
        for field in fields:
            self.assertEqual(self.mapping['properties'][field], mapping)

    @mock.patch('daybed.indexer.logger.error')
    def test_generated_mapping_generates_no_error(self, error_mock):
        self.app.put_json('/models/test', self.model,
                          headers=self.headers)
        self.assertFalse(error_mock.called)

    def test_all_field_types_are_used_in_definition(self):
        all_fields = registry.names
        used_fields = [f['type'] for f in self.model['definition']['fields']]
        self.assertEqual(set(all_fields), set(used_fields))

    def test_default_mapping_is_string(self):
        strings = ['d', 'e', 'f', 'j', 'm', 'n', 'o', 'p', 'v', 'w']
        self.assertFieldMapping(strings, {'type': 'string'})

    def test_object_fields_are_mapped_with_properties(self):
        self.assertFieldMapping('q',
                                {'type': 'object',
                                 'properties': {'qq': {'type': 'integer'}}})

    def test_group_fields_are_mapped_as_first_level_fields(self):
        self.assertFieldMapping('i', {'type': 'integer'})

    def test_json_mappings(self):
        self.assertFieldMapping(['k'], {'type': 'object', 'enabled': False})

    def test_integer_mappings(self):
        self.assertFieldMapping(['a', 'l'], {'type': 'integer'})

    def test_date_mappings(self):
        self.assertFieldMapping(['g', 'h'], {'type': 'date'})

    def test_boolean_mappings(self):
        self.assertFieldMapping('b', {'type': 'boolean'})

    def test_float_mappings(self):
        self.assertFieldMapping('c', {'type': 'float'})

    def test_geospatial_mappings(self):
        self.assertFieldMapping(['r', 's', 'u'], {'type': 'geo_shape'})
        self.assertFieldMapping('t', {'type': 'geo_point'})


class RecordMappingTest(BaseWebTest):

    def setUp(self):
        super(RecordMappingTest, self).setUp()

        self.app.put_json('/models/simple', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.put_json('/models/simple/records/simple-rec', MODEL_RECORD,
                          headers=self.headers)
        self.app.put_json('/models/test', ALL_FIELDS_DEFINITION,
                          headers=self.headers)

        self.record = {
            'a': 0,
            'b': False,
            'c': 3.14,
            'd': 'tanga',
            'e': 'lorem ipsum',
            'f': 'http://mit.edu',
            'g': '2014-08-17',
            'h': '2014-08-17 16:11:03',
            'i': 42,
            'j': 'me@home.org',
            'k': '{"foo": "blah"}',
            'l': 11,
            'm': 'a',
            'n': 'a',
            'o': ':)',
            'p': [{"pp": 1}],
            'q': {"qq": 1},
            'r': {"type": "Point", "coordinates": [0.0, 1.0]},
            's': [[0.0, 0.0], [1.0, 1.0]],
            't': [0.0, 1.0],
            'u': [[[0.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
            'v': ["simple-rec"],
            'w': 'simple-rec',
        }

        self.app.put_json('/models/test/records/1', self.record,
                          headers=self.headers)

        self.mapping = None
        with mock.patch('elasticsearch.client.Elasticsearch.index') as mocked:
            self.app.put_json('/models/test/records/1', self.record,
                              headers=self.headers)
            index_call = mocked.call_args_list[0]
            self.mapping = index_call[1]['body']

    @mock.patch('daybed.indexer.logger.error')
    def test_generated_mapping_generates_no_error(self, error_mock):
        self.app.put_json('/models/test/records/1', self.record,
                          headers=self.headers)
        self.assertFalse(error_mock.called)

    def test_list_are_indexed_as_strings(self):
        self.assertEqual(self.mapping['p'], '[{"pp": 1}]')

    def test_line_and_polygon_are_converted_to_geojson(self):
        self.assertEqual(self.mapping['s'],
                         {"type": "Linestring",
                          "coordinates": self.record['s']})
        self.assertEqual(self.mapping['u'],
                         {"type": "Polygon",
                          "coordinates": self.record['u']})
