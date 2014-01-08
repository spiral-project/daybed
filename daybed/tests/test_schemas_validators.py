import colander

from daybed.schemas.validators import RolesValidator
from daybed.tests.support import unittest


class RolesValidatorTests(unittest.TestCase):
    def test_roles(self):
        schema = RolesValidator()
        self.assertRaises(colander.Invalid, schema.deserialize, {})
        self.assertRaises(colander.Invalid, schema.deserialize,
                          {'admins': 'not-a-sequence'})
        self.assertEquals(schema.deserialize(
            {'admins': ['Remy', 'Alexis']}),
            {'admins': ['Remy', 'Alexis']})

        return
        # XXX: FIXME
        self.assertRaises(colander.Invalid, schema.deserialize,
                          {'admins': ['Test'],
                           'group:toto': 'not-a-sequence'})
