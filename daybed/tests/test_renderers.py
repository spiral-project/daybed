import json

from pyramid import testing

from daybed.renderers import GeoJSON
from .support import BaseWebTest


class TestGeoJSONRenderer(BaseWebTest):

    def setUp(self):
        super(TestGeoJSONRenderer, self).setUp()
        self.name = 'locations'
        self.roles = {'admins': ['group:pirates']}
        self.definition = {
            "fields": [{"name": "location", "type": "point"}]
        }
        self.db.put_model(self.definition, self.roles,
                          'admin-only', self.name)

        self.geojson = GeoJSON()
        self.renderer = self.geojson(None)

    def _build_request(self):
        request = testing.DummyRequest()
        request.matchdict['model_id'] = self.name
        request.db = self.db
        return request

    def _rendered(self, data, request):
        system = {'request': request}
        return self.renderer(data, system)

    def assertJSONEqual(self, a, b):
        self.assertDictEqual(json.loads(a), b)

    def test_geojson_renderer_with_empty_collection(self):
        request = self._build_request()
        geojson = self._rendered({'data': []}, request)
        self.assertJSONEqual(geojson,
                             {"type": "FeatureCollection", "features": []})

    def test_geojson_renderer_works_with_jsonp(self):
        request = self._build_request()
        request.GET['callback'] = 'func'
        geojsonp = self._rendered({'data': [{'location': [0, 0]}]}, request)
        self.assertIn('func(', geojsonp)
