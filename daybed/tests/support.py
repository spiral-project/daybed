import os
from uuid import uuid4
try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

import webtest
from daybed.db import DatabaseConnection


HERE = os.path.dirname(os.path.abspath(__file__))


class BaseWebTest(unittest.TestCase):
    """Base Web Test to test your cornice service.

    It setups the database before each test and delete it after.
    """

    def setUp(self):

        self.db_name = os.environ['DB_NAME'] = 'daybed-tests-%s' % uuid4()
        self.app = webtest.TestApp("config:tests.ini", relative_to=HERE)
        self.db_server = self.app.app.registry.settings['db_server']
        self.db_base = self.db_server[self.db_name]
        self.db = DatabaseConnection(self.db_base)

    def tearDown(self):
        # Delete Test DB
        self.db_server.delete(self.db_name)

    def put_valid_definition(self):
        """Create a valid definition named "todo".
        """
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)
