import collections
try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA
import base64

import six
import webtest

from daybed.backends.exceptions import UserAlreadyExist


class BaseWebTest(unittest.TestCase):
    """Base Web Test to test your cornice service.

    It setups the database before each test and delete it after.
    """

    def setUp(self):
        self.app = webtest.TestApp("config:conf/tests.ini", relative_to='.')
        self.db = self.app.app.registry.backend

        try:
            self.db.add_user({'name': 'admin', 'apitoken': 'foo'})
        except UserAlreadyExist:
            pass

        auth_password = base64.b64encode(
            u'admin:foo'.encode('ascii')).strip().decode('ascii')
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic {0}'.format(auth_password),
        }

    def tearDown(self):
        self.db.delete_db()


def force_unicode(data):
    """ Recursively force unicode.

    Works for dict keys, list values etc.
    (source: http://stackoverflow.com/questions/1254454/)
    """
    if isinstance(data, six.string_types):
        return six.text_type(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(force_unicode, six.iteritems(data)))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(force_unicode, data))
    else:
        return data
