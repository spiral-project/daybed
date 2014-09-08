import collections
try:
    import unittest2 as unittest
except ImportError:
    import unittest  # NOQA
import base64

import six
import webtest

from daybed import __version__
from daybed.tokens import get_hawk_credentials


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '/v%s%s' % (__version__.split('.')[0], path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):
    """Base Web Test to test your cornice service.

    It setups the database before each test and delete it after.
    """

    def setUp(self):
        self.app = webtest.TestApp("config:conf/tests.ini", relative_to='.')
        self.app.RequestClass = PrefixedRequestClass

        self.db = self.app.app.registry.backend
        self.indexer = self.app.app.registry.index

        token, self.credentials = get_hawk_credentials()
        self.db.store_credentials(token, self.credentials)

        auth_password = base64.b64encode(
            (u'%s:%s' % (self.credentials['id'],
                         self.credentials['key'])).encode('ascii')) \
            .strip().decode('ascii')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic {0}'.format(auth_password),
        }

    def tearDown(self):
        self.db.delete_db()
        self.indexer.delete_indices()


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
