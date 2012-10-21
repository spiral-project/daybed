import os
from unittest import TestCase
import webtest


HERE = os.path.dirname(os.path.abspath(__file__))

class BaseWebTest(TestCase):
    """Base Web Test to test your cornice service."""

    def setUp(self):
        self.app = webtest.TestApp("config:tests.ini", relative_to=HERE)
        self.db_server = self.app.app.registry.settings['db_server']

    def tearDown(self):
        # Delete Test DB
        del self.db_server[self.app.app.registry.settings['db_name']]
