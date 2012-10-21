import os
from unittest import TestCase
import webtest


HERE = os.path.dirname(os.path.abspath(__file__))


class BaseWebTest(TestCase):
    """Base Web Test to test your cornice service.

    It setups the database before each test and delete it after.
    """

    def setUp(self):
        self.app = webtest.TestApp("config:tests.ini", relative_to=HERE)
        self.db_server = self.app.app.registry.settings['db_server']

    def tearDown(self):
        # Delete Test DB
        del self.db_server[self.app.app.registry.settings['db_name']]

    def put_valid_definition(self):
        """Create a valid definition named "todo".
        """
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)
