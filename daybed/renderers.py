from pyramid.renderers import JSON


class GeoJSON(JSON):
    def __call__(self, info):
        def _render(value, system):
            request = system.get('request')
            if request is not None:
                response = request.response
                ct = response.content_type
                if ct == response.default_content_type:
                    # GeoJSON is JSON.
                    response.content_type = 'application/json'
            default = self._make_default(request)

            # Inspect model definition
            geom_fields = {}
            model_id = request.matchdict.get('model_id')
            if model_id:
                definition = request.db.get_model_definition(model_id)
                if definition:
                    geom_fields = self._geomFields(definition)

            # Transform records into GeoJSON feature collection
            records = value.get('data')

            if records:
                geojson = dict(type='FeatureCollection', features=[])
                for record in records:
                    feature = self._buildFeature(geom_fields, record)
                    geojson['features'].append(feature)
                value = geojson

            return self.serializer(value, default=default, **self.kw)

        return _render

    def _geomFields(self, definition):
        """Returns mapping between definition field names and geometry types
        """
        # Supported geometry types
        mapping = {'point': 'Point',
                   'line': 'Linestring',
                   'polygon': 'Polygon'}
        # Gather all geometry fields for this definition
        geom_fields = dict()
        for field in definition['fields']:
            if field['type'] in mapping.keys():
                geom_fields[field['name']] = mapping.get(field['type'],
                                                         field['type'])
        return geom_fields

    def _buildFeature(self, geom_fields, record):
        """Return GeoJSON feature (properties + geometry(ies))
        """
        feature = dict(type='Feature')
        feature['id'] = record.pop('id', None)
        first = True
        for name, geomtype in geom_fields.items():
            coords = record.pop(name)
            name = 'geometry' if first else name
            # Note for future: this won't work for GeometryCollection
            geometry = dict(type=geomtype, coordinates=coords)
            feature[name] = geometry
            first = False
        feature['properties'] = record
        return feature
