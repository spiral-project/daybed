import json

import elasticsearch
from elasticsearch.exceptions import ElasticsearchException

from daybed import events, logger


class DaybedIndexer(object):

    def __init__(self, config, hosts):
        self.client = elasticsearch.Elasticsearch(hosts)

        config.add_subscriber(self._create_index, events.ModelCreated)
        config.add_subscriber(self._update_index, events.ModelUpdated)
        config.add_subscriber(self._delete_index, events.ModelDeleted)
        config.add_subscriber(self._index_record, events.RecordCreated)
        config.add_subscriber(self._reindex_record, events.RecordUpdated)
        config.add_subscriber(self._unindex_record, events.RecordDeleted)

    def search(self, *args, **kwargs):
        try:
            return self.client.search(*args, **kwargs)
        except ElasticsearchException as e:
            logger.error(e)
            return {}

    def _create_index(self, event):
        if not self.client.indices.exists(index=event.model_id):
            logger.debug("Create index for model '%s'" % event.model_id)
            self.client.indices.create(index=event.model_id)

        logger.debug("Create mapping for model '%s'" % event.model_id)
        self.__put_mapping(event.request, event.model_id)

    def _update_index(self, event):
        logger.debug("Update mapping of model '%s'" % event.model_id)
        try:
            self.client.indices.delete_mapping(index=event.model_id,
                                               doc_type=event.model_id)
        except ElasticsearchException as e:
            logger.error(e)
        self.__put_mapping(event.request, event.model_id)

    def _delete_index(self, event):
        logger.debug("Delete index of model '%s'" % event.model_id)
        try:
            self.client.indices.delete(index=event.model_id)
        except ElasticsearchException as e:
            logger.error(e)

    def _index_record(self, event):
        logger.debug("Index record %s of model '%s'" % (event.record_id,
                                                        event.model_id))
        self.__index(event.request, event.model_id, event.record_id)

    def _reindex_record(self, event):
        logger.debug("Reindex record %s of model '%s'" % (event.record_id,
                                                          event.model_id))
        self.__index(event.request, event.model_id, event.record_id)

    def _unindex_record(self, event):
        logger.debug("Unindex record %s of model '%s'" % (event.record_id,
                                                          event.model_id))
        try:
            self.client.delete(index=event.model_id,
                               doc_type=event.model_id,
                               id=event.record_id,
                               refresh=True)
        except ElasticsearchException as e:
            logger.error(e)

    def __put_mapping(self, request, model_id):
        """ Transforms the model definition into an Elasticsearch mapping,
        and associate to its index.
        """
        model_definition = request.db.get_model_definition(model_id)
        mapping_definition = self._definition_as_mapping(model_definition)
        try:
            mapping = self.client.indices.put_mapping(index=model_id,
                                                      doc_type=model_id,
                                                      body=mapping_definition)
            return mapping
        except ElasticsearchException as e:
            logger.error(e)

    def __index(self, request, model_id, record_id):
        """ Transforms the record to an ElasticSearch record compatible with
        the mapping built from its model definition.
        """
        definition = request.db.get_model_definition(model_id)
        record = request.db.get_record(model_id, record_id)
        mapping_record = self._record_as_mapping(definition, record)
        try:
            index = self.client.index(index=model_id,
                                      doc_type=model_id,
                                      id=record_id,
                                      body=mapping_record,
                                      refresh=True)
            return index
        except ElasticsearchException as e:
            logger.error(e)

    def _definition_as_mapping(self, model_definition):
        mapping = {
            'properties': {}
        }
        fields = model_definition['fields']
        index_types = {
            'int': 'integer',
            'range': 'integer',
            'date': 'date',
            'datetime': 'date',
            'boolean': 'boolean',
            'decimal': 'float',
            'point': 'geo_point',
            'line': 'geo_shape',
            'polygon': 'geo_shape',
            'geojson': 'geo_shape',
            'json': 'object',
            'object': 'object',
        }
        for field in fields:
            name = field.get('name')
            daybed_type = field.get('type')

            if daybed_type == 'group':
                for subfield in field['fields']:
                    subname = subfield['name']
                    subtype = subfield['type']
                    index_type = index_types.get(subtype, 'string')
                    mapping['properties'][subname] = {'type': index_type}
                continue

            index_type = index_types.get(daybed_type, 'string')
            mapping['properties'][name] = {'type': index_type}

            if daybed_type == 'json':
                mapping['properties'][name]['enabled'] = False

            if daybed_type == 'object':
                properties = {}
                for subfield in field['fields']:
                    subname = subfield['name']
                    subtype = subfield['type']
                    index_type = index_types.get(subtype, 'string')
                    properties[subname] = {'type': index_type}
                mapping['properties'][name]['properties'] = properties

        return mapping

    def _record_as_mapping(self, definition, record):
        field_types = {}
        for field in definition['fields']:
            field_name = field.get('name')
            field_type = field['type']
            field_types[field_name] = field_type

        mapping = record.copy()
        for key, value in mapping.items():
            field_type = field_types.get(key)
            if field_type in ('line', 'polygon'):
                geojson = {
                    'line': 'Linestring',
                    'polygon': 'Polygon'
                }
                mapping[key] = {
                    'type': geojson[field_type],
                    'coordinates': value
                }
            if field_type in ('list',):
                mapping[key] = json.dumps(value)
        return mapping
