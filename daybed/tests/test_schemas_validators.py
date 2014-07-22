import mock
from cornice.errors import Errors
from pyramid.testing import DummyRequest

from daybed.schemas.validators import validator
from daybed.tests.support import unittest


class ValidatorTests(unittest.TestCase):
    def test_adds_body_error_if_json_invalid(self):
        request = DummyRequest()
        request.body = b'{wrong,"format"}'
        request.errors = Errors()
        validator(request, mock.Mock())
        self.assertEqual('body', request.errors[0]['location'])
