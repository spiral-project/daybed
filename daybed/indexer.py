import elasticsearch
from elasticsearch.exceptions import ElasticsearchException

from daybed import events, logger


class DaybedIndexer(object):

    def __init__(self, config, hosts):
        self.client = elasticsearch.Elasticsearch(hosts)

        config.add_subscriber(self._create_index, events.ModelCreated)
        config.add_subscriber(self._delete_index, events.ModelDeleted)
        config.add_subscriber(self._index_record, events.RecordCreated)
        config.add_subscriber(self._unindex_record, events.RecordDeleted)

    def search(self, *args, **kwargs):
        try:
            return self.client.search(*args, **kwargs)
        except ElasticsearchException as e:
            logger.error(e)
            return {}

    def refresh(self, index='_all'):
        """ Refresh indices manually, instead of waiting for periodical refresh.
        http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/indices-refresh.html
        """
        self.client.indices.refresh(index=index)

    def _create_index(self, event):
        logger.debug("Create index for model '%s'" % event.model_id)
        request = event.request

        if not self.client.indices.exists(index=event.model_id):
            self.client.indices.create(index=event.model_id)

        model_definition = request.db.get_model_definition(event.model_id)
        mapping_definition = self._definition_as_mapping(model_definition)
        try:
            mapping = self.client.indices.put_mapping(index=event.model_id,
                                                      doc_type=event.model_id,
                                                      body=mapping_definition)
            return mapping
        except ElasticsearchException as e:
            logger.error(e)

    def _delete_index(self, event):
        logger.debug("Delete index of model '%s'" % event.model_id)
        # XXX

    def _index_record(self, event):
        logger.debug("Index record %s of model '%s'" % (event.record_id,
                                                        event.model_id))
        request = event.request
        definition = request.db.get_model_definition(event.model_id)
        record = request.db.get_record(event.model_id,
                                       event.record_id)
        mapping_record = self._record_as_mapping(definition, record)
        try:
            index = self.client.index(index=event.model_id,
                                      doc_type=event.model_id,
                                      id=event.record_id,
                                      body=mapping_record)
            return index
        except ElasticsearchException as e:
            logger.error(e)

    def _unindex_record(self, event):
        logger.debug("Unindex record %s of model '%s'" % (event.record_id,
                                                          event.model_id))
        # XXX

    def _definition_as_mapping(self, model_definition):
        mapping_definition = {
            'properties': {}
        }
        fields = model_definition['fields']
        index_types = {
            'int': 'integer',
            'date': 'date',
            'boolean': 'boolean',
            'decimal': 'float',
            'point': 'geo_point',
            'line': 'geo_shape',
            'polygon': 'geo_shape',
            'geojson': 'geo_shape',
            'object': 'object',
        }
        for field in fields:
            name = field['name']
            daybed_type = field.get('type')
            index_type = index_types.get(daybed_type, 'string')
            mapping_definition['properties'][name] = {'type': index_type}
        return mapping_definition

    def _record_as_mapping(self, definition, record):
        field_types = {}
        for field in definition['fields']:
            field_name = field['name']
            field_type = field['type']
            field_types[field_name] = field_type

        mapping_record = record.copy()
        for key, value in mapping_record.items():
            field_type = field_types.get(key)
            if field_type in ('line', 'polygon'):
                mapping_record[key] = {
                    'type': field_type,
                    'coordinates': value
                }
        return mapping_record