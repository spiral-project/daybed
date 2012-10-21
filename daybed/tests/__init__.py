import os
from unittest import TestCase
import webtest


HERE = os.path.dirname(os.path.abspath(__file__))

class BaseWebTest(TestCase):
    """Base Web Test to test your cornice service."""
    def __init__(self, *args, **kwargs):
        super(BaseWebTest, self).__init__(*args, **kwargs)
        self.headers = {'Content-Type': 'application/json'}

    def setUp(self):
        self.app = webtest.TestApp("config:tests.ini", relative_to=HERE)

    def tearDown(self):
        # Delete Test DB
        db_server = self.app.app.registry.settings['db_server']
        del db_server[self.app.app.registry.settings['db_name']]
