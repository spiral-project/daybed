try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from collections import defaultdict

from pyramid.renderers import JSONP


class JSONSchema(JSONP):
    """Renderer for JSON Schema"""
    fields = {
        'int': 'integer',
        'text': 'string',
    }

    def __call__(self, info):
        def _get_field(field):
            type = field.get('type')
            field = {
                'description': field.get('label', field.get('name')),
                'type': self.fields.get(type, type)
            }
            return field

        def _render(definition, system):
            properties = defaultdict(dict)
            required = []

            for field in definition['fields']:
                properties[field['name']] = _get_field(field)

                if field['required']:
                    required.append(field['name'])

            jsonschema = {
                '$schema': 'http://json-schema.org/schema#',
                'title': definition['title'],
                'description': definition['description'],
                'type': 'object',
                'properties': properties,
                'required': required
            }
            jsonp = super(JSONSchema, self).__call__(info)
            return jsonp(jsonschema, system)

        return _render


class GeoJSON(JSONP):
    def __call__(self, info):
        def _render(value, system):
            request = system.get('request')

            # Response should have appropriate Content-Type
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'application/vnd.geo+json'

            # Inspect model definition
            geom_fields = {}
            model_id = request.matchdict.get('model_id')
            if model_id:
                definition = request.db.get_model_definition(model_id)
                if definition:
                    geom_fields = self._geomFields(definition)

            # Transform records into GeoJSON feature collection
            records = value.get('records')

            if records is not None:
                geojson = dict(type='FeatureCollection', features=[])
                for record in records:
                    feature = self._buildFeature(geom_fields, record)
                    geojson['features'].append(feature)
                value = geojson

            jsonp = super(GeoJSON, self).__call__(info)
            return jsonp(value, system)

        return _render

    def _geomFields(self, definition):
        """Returns mapping between definition field names and geometry types
        """
        # Supported geometry types
        mapping = {'point': 'Point',
                   'line': 'Linestring',
                   'polygon': 'Polygon'}
        geom_types = ['geojson'] + list(mapping.keys())
        # Gather all geometry fields for this definition
        geom_fields = []
        for field in definition['fields']:
            if field['type'] in geom_types:
                geom_fields.append((field['name'],
                                    mapping.get(field['type'],
                                                field['type'])))
        return OrderedDict(geom_fields)

    def _buildFeature(self, geom_fields, record):
        """Return GeoJSON feature (properties + geometry(ies))
        """
        feature = dict(type='Feature')
        feature['id'] = record.pop('id', None)
        first = True
        for name, geomtype in geom_fields.items():
            if geomtype == 'geojson':
                geometry = record.pop(name)
            else:
                # Note for future: this won't work for GeometryCollection
                coords = record.pop(name)
                geometry = dict(type=geomtype, coordinates=coords)
            name = 'geometry' if first else name
            feature[name] = geometry
            first = False
        feature['properties'] = record
        return feature
