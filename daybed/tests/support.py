try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA

import webtest

from daybed.backends.couch_db.database import Database


class BaseWebTest(unittest.TestCase):
    """Base Web Test to test your cornice service.

    It setups the database before each test and delete it after.
    """

    def setUp(self):

        self.app = webtest.TestApp("config:tests.ini", relative_to='.')
        self.backend = self.app.app.registry.backend
        self.db = Database(self.backend.db)

    def tearDown(self):
        self.backend.delete_db()

    def put_valid_definition(self):
        """Create a valid definition named "todo".
        """
        # Put a valid definition
        self.app.put_json('/definitions/todo',
                          self.valid_definition,
                          headers=self.headers)
