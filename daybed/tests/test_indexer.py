import decimal
import json
import copy
import mock

from daybed.schemas import registry
from daybed import indexer

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

    @mock.patch('daybed.indexer.logger.error')
    @mock.patch('elasticsearch.client.indices.IndicesClient.put_mapping')
    def test_no_exception_on_model_put_when_index_fails(self,
                                                        error_mock,
                                                        put_mapping_mock):
        put_mapping_mock.side_effect = indexer.ElasticsearchException
        self.app.put_json('/models/test-1', MODEL_DEFINITION,
                          headers=self.headers)
        self.assertTrue(error_mock.called)

    @mock.patch('daybed.indexer.logger.error')
    @mock.patch('elasticsearch.client.indices.IndicesClient.exists')
    def test_no_exception_on_model_put_when_lookup_fails(self,
                                                         exists_mock,
                                                         error_mock):
        exists_mock.side_effect = indexer.ElasticsearchException
        self.app.post_json('/models', MODEL_DEFINITION,
                           headers=self.headers)
        self.assertTrue(error_mock.called)

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
        delete_index_mock.assert_called_with(
            index=self.app.app.registry.index.prefix('test')
        )

    @mock.patch('daybed.indexer.logger.error')
    @mock.patch('elasticsearch.client.indices.IndicesClient.delete')
    def test_no_exception_on_model_deletion_when_index_fails(self,
                                                             delete_mock,
                                                             error_mock):
        delete_mock.side_effect = indexer.ElasticsearchException
        self.app.put_json('/models/test', MODEL_DEFINITION,
                          headers=self.headers)
        self.app.delete('/models/test',
                        headers=self.headers)
        self.assertTrue(error_mock.called)

    @mock.patch('daybed.indexer.logger.error')
    @mock.patch('elasticsearch.client.cat.CatClient.indices')
    def test_no_exception_when_indices_deletion_fails(self,
                                                      indices_mock,
                                                      error_mock):
        indices_mock.side_effect = indexer.ElasticsearchException
        self.indexer.delete_indices()
        self.assertTrue(error_mock.called)


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
        delete_mock.assert_called_with(
            index=self.app.app.registry.index.prefix('test'),
            doc_type='test',
            id='1', refresh=True
        )

    @mock.patch('daybed.indexer.logger.error')
    @mock.patch('elasticsearch.client.Elasticsearch.delete')
    def test_no_exception_on_record_deletion_when_index_fails(self,
                                                              error_mock,
                                                              delete_mock):
        delete_mock.side_effect = indexer.ElasticsearchException
        self.app.put_json('/models/test/records/1', MODEL_RECORD,
                          headers=self.headers)
        self.app.delete('/models/test/records/1',
                        headers=self.headers)
        self.assertTrue(error_mock.called)

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
        'description': 'Use all types in one definition',
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
        self.app.post_json('/models', self.model,
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

        self.mapping = None
        with mock.patch('elasticsearch.client.Elasticsearch.index') as mocked:
            self.app.put_json('/models/test/records/1', self.record,
                              headers=self.headers)
            index_call = mocked.call_args_list[0]
            self.mapping = index_call[1]['body']

    @mock.patch('daybed.indexer.logger.error')
    def test_generated_mapping_generates_no_error(self, error_mock):
        self.app.post_json('/models/test/records', self.record,
                           headers=self.headers)
        self.assertFalse(error_mock.called)

    def test_indexed_record_is_kept_in_source(self):
        self.app.post_json('/models/test/records', self.record,
                           headers=self.headers)
        response = self.app.get('/models/test/search/',
                                headers=self.headers)
        result = response.json['hits']['hits'][0]['_source']
        result['id'] = self.mapping['id']  # id may differ
        result['c'] = decimal.Decimal(str(result['c']))  # ES float
        for k, v in self.mapping.items():
            self.assertEqual(result[k], v)

    def test_list_are_indexed_as_strings(self):
        self.assertEqual(self.mapping['p'], '[{"pp": 1}]')

    def test_line_and_polygon_are_converted_to_geojson(self):
        self.assertEqual(self.mapping['s'],
                         {"type": "Linestring",
                          "coordinates": self.record['s']})
        self.assertEqual(self.mapping['u'],
                         {"type": "Polygon",
                          "coordinates": self.record['u']})


class SpatialSearchTest(BaseWebTest):

    def setUp(self):
        super(SpatialSearchTest, self).setUp()

        definition = copy.deepcopy(MODEL_DEFINITION)
        definition['definition']['fields'] = [{
            'name': 'geom',
            'type': 'point'
        }]
        self.app.put_json('/models/location', definition,
                          headers=self.headers)
        self.app.put_json('/models/location/records/0', {'geom': [0, 0]},
                          headers=self.headers)
        self.app.put_json('/models/location/records/1', {'geom': [1, 1]},
                          headers=self.headers)
        self.app.put_json('/models/location/records/2', {'geom': [2, 2]},
                          headers=self.headers)

    def spatialSearch(self, bbox):
        query = {'filter': {'geo_bounding_box': {'geom': bbox}}}
        query = {'query': {'filtered': query}}
        resp = self.app.request('/models/location/search/',
                                method='GET',
                                body=json.dumps(query).encode(),
                                headers=self.headers)
        results = resp.json.get('hits', {}).get('hits', [])
        return results

    def test_no_result_if_bbox_disjoint_with_records(self):
        bbox_none = {
            'top_left': {'lon': 10, 'lat': 20},
            'bottom_right': {'lon': 20, 'lat': 10},
        }
        results = self.spatialSearch(bbox_none)
        self.assertEqual(len(results), 0)

    def test_filters_records_by_position(self):
        bbox_match = {
            'top_left': {'lon': -0.5, 'lat': 1.5},
            'bottom_right': {'lon': 1.5, 'lat': -0.5},
        }
        results = self.spatialSearch(bbox_match)
        self.assertEqual(len(results), 2)
