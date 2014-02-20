import json

from pyramid import testing

from daybed.renderers import GeoJSON
from .support import BaseWebTest


class TestGeoJSONRenderer(BaseWebTest):

    def setUp(self):
        super(TestGeoJSONRenderer, self).setUp()
        name = 'simple'
        self.roles = {'admins': ['group:pirates']}
        self.definition = {
            "fields": [{"name": "location", "type": "point"}]
        }
        self.db.put_model(self.definition, self.roles, 'admin-only', name)

        self.geojson = GeoJSON()
        self.renderer = self.geojson(None)
        self.request = testing.DummyRequest()
        self.request.matchdict['model_id'] = name
        self.request.db = self.db
        self.system = {'request': self.request}

    def assertJSONEqual(self, a, b):
        self.assertDictEqual(json.loads(a), b)

    def test_geojson_renderer_with_empty_collection(self):
        geojson = self.renderer({'data': []}, self.system)
        self.assertJSONEqual(geojson,
                             {"type": "FeatureCollection", "features": []})
