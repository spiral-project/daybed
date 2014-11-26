from __future__ import absolute_import, unicode_literals
from pyramid.i18n import TranslationString as _
from pyramid.threadlocal import get_current_request

from colander import Invalid, String
from daybed.backends.exceptions import UserIdNotFound
from . import registry, TypeField, get_db

__all__ = ['UserIdField']


class UserIdIsValid(object):
    def __init__(self, user_id):
        self.user_id = user_id

    def __call__(self, node, value):
        if self.user_id != value:
            msg = "%s is a wrong user_id, it should be %s." % (
                value, self.user_id
            )
            raise Invalid(node, msg)


@registry.add('userid')
class UserIdField(TypeField):
    """An email address field."""
    node = String
    hint = _('An automatic user id field. '
             'Can be the validated email address for this account. '
             'Fallback to the HawkId')

    @classmethod
    def validation(cls, **kwargs):
        request = get_current_request()
        db = get_db()

        try:
            user_id = db.get_user_id(request.authenticated_userid)
        except UserIdNotFound:
            user_id = request.authenticated_userid

        kwargs['missing'] = user_id
        kwargs['validator'] = UserIdIsValid(user_id)

        return super(UserIdField, cls).validation(**kwargs)
