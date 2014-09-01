import json

import elasticsearch
from elasticsearch.exceptions import ElasticsearchException

from daybed import logger


class ElasticSearchIndexer(object):

    def __init__(self, hosts, prefix):
        self.client = elasticsearch.Elasticsearch(hosts)
        self.prefix = lambda x: u'%s_%s' % (prefix, x)

    def search(self, model_id, query, params):
        supported_params = ['sort', 'from', 'source', 'fields']
        params = dict([p for p in params.items() if p[0] in supported_params])
        return self.client.search(index=self.prefix(model_id),
                                  doc_type=model_id,
                                  body=query,
                                  **params)

    def on_model_created(self, event):
        if not self.client.indices.exists(index=self.prefix(event.model_id)):
            logger.debug("Create index for model '%s'" % event.model_id)
            self.client.indices.create(index=self.prefix(event.model_id))

        logger.debug("Create mapping for model '%s'" % event.model_id)
        definition = event.request.db.get_model_definition(event.model_id)
        self.__put_mapping(event.model_id, definition)

    def on_model_updated(self, event):
        logger.debug("Update mapping of model '%s'" % event.model_id)
        try:
            self.client.indices.delete_mapping(
                index=self.prefix(event.model_id),
                doc_type=event.model_id
            )
        except ElasticsearchException as e:
            logger.error(e)
        definition = event.request.db.get_model_definition(event.model_id)
        self.__put_mapping(event.model_id, definition)

    def on_model_deleted(self, event):
        logger.debug("Delete index of model '%s'" % event.model_id)
        try:
            self.client.indices.delete(index=self.prefix(event.model_id))
        except ElasticsearchException as e:
            logger.error(e)

    def on_record_created(self, event):
        logger.debug("Index record %s of model '%s'" % (event.record_id,
                                                        event.model_id))
        definition = event.request.db.get_model_definition(event.model_id)
        record = event.request.db.get_record(event.model_id, event.record_id)
        self.__index(event.model_id, definition, event.record_id, record)

    def on_record_updated(self, event):
        logger.debug("Reindex record %s of model '%s'" % (event.record_id,
                                                          event.model_id))
        definition = event.request.db.get_model_definition(event.model_id)
        record = event.request.db.get_record(event.model_id, event.record_id)
        self.__index(event.model_id, definition, event.record_id, record)

    def on_record_deleted(self, event):
        logger.debug("Unindex record %s of model '%s'" % (event.record_id,
                                                          event.model_id))
        try:
            self.client.delete(index=self.prefix(event.model_id),
                               doc_type=event.model_id,
                               id=event.record_id,
                               refresh=True)
        except ElasticsearchException as e:
            logger.error(e)

    def delete_indices(self):
        logger.debug("Drop the index on database deleted event.")
        try:
            fullnames = self.client.cat.indices().split('\n')[:-1]
            indices = [x.split()[1] for x in fullnames]
            prefixed_indices = [indice for indice in indices
                                if indice.startswith(self.prefix(''))]
            if len(prefixed_indices) > 0:
                self.client.indices.delete(index=','.join(prefixed_indices))
        except ElasticsearchException as e:
            logger.error(e)

    def __put_mapping(self, model_id, definition):
        """ Transforms the model definition into an Elasticsearch mapping,
        and associate to its index.
        """
        mapping_definition = self._definition_as_mapping(definition)
        try:
            mapping = self.client.indices.put_mapping(
                index=self.prefix(model_id),
                doc_type=model_id,
                body=mapping_definition
            )
            return mapping
        except ElasticsearchException as e:
            logger.error(e)

    def __index(self, model_id, definition, record_id, record):
        """ Transforms the record to an ElasticSearch record compatible with
        the mapping built from its model definition.
        """
        mapping_record = self._record_as_mapping(definition, record)
        try:
            index = self.client.index(index=self.prefix(model_id),
                                      doc_type=model_id,
                                      id=record_id,
                                      body=mapping_record,
                                      refresh=True)
            return index
        except ElasticsearchException as e:
            logger.error(e)

    def _definition_as_mapping(self, definition):
        fields = definition['fields']
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

        def field_list(fields):
            mappings = {}
            for field in fields:
                fieldname = field.get('name')
                fieldtype = field.get('type')
                mapping = {'type': index_types.get(fieldtype, 'string')}
                if fieldtype == 'json':
                    mapping['enabled'] = False
                if fieldtype == 'group':
                    mappings.update(field_list(field['fields']))
                    continue
                if fieldtype == 'object':
                    mapping['properties'] = field_list(field['fields'])
                mappings[fieldname] = mapping
            return mappings

        mapping = {
            'properties': field_list(fields)
        }
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
            if field_type == 'point':
                mapping[key] = {'lon': value[0], 'lat': value[1]}
            if field_type == 'list':
                mapping[key] = json.dumps(value)
        return mapping
