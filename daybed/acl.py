from pyramid.interfaces import IAuthorizationPolicy
from pyramid.security import Authenticated, Everyone
from zope.interface import implementer

from daybed.backends.exceptions import (
    ModelNotFound, RecordNotFound, UserNotFound
)
from daybed import logger


class Any(list):
    def matches(self, permissions):
        check = False
        for perm in self:
            if hasattr(perm, 'matches'):
                check |= perm.matches(permissions)
            else:
                check |= perm in permissions
        return check


class All(list):
    def matches(self, permissions):
        check = True
        for perm in self:
            if hasattr(perm, 'matches'):
                check &= perm.matches(permissions)
            else:
                check &= perm in permissions
        return check


AUTHORS_PERMISSIONS = set(['update_my_record', 'delete_my_record',
                           'read_my_record'])

VIEWS_PERMISSIONS_REQUIRED = {
    'post_model':     All(['create_model']),
    'get_model':      All(['read_definition', 'read_acls']),
    'put_model':      All(['create_model', 'update_definition', 'update_acls',
                           'delete_model']),
    'delete_model':   All(['delete_model']),
    'get_definition': All(['read_definition']),
    'post_record':    All(['create_record']),
    'get_records':    All(['read_all_records']),
    'delete_records': All(['delete_all_records']),
    'get_record':     Any(['read_my_record', 'read_all_records']),
    'put_record':     All(['create_record',
                           Any(['update_my_record', 'update_all_records']),
                           Any(['delete_my_record', 'delete_all_records'])]),
    'patch_record':   Any(['update_my_record', 'update_all_records']),
    'delete_record':  Any(['delete_my_record', 'delete_all_records']),
}


@implementer(IAuthorizationPolicy)
class DaybedAuthorizationPolicy(object):

    def permits(self, context, principals, permission):
        """Returns True or False depending if the user with the specified
        principals has access to the given permission.
        """
        permissions_required = VIEWS_PERMISSIONS_REQUIRED[permission]

        user_permissions = set()

        if context.model_id:
            try:
                acls = context.db.get_model_acls(context.model_id)
            except ModelNotFound:
                #  In case the model doesn't exist, you have access to it.
                # PUT a non existing model
                return True
        else:
            # POST a model
            return True

        for acl_name, tokens in acls.items():
            # If one of the principals is in the valid tokens for this,
            # permission, grant the permission.
            if set(principals) & set(tokens):
                user_permissions.add(acl_name)

        logger.debug("user permissions: %s", user_permissions)

        if context.record_id is not None:
            try:
                authors = context.db.get_record_authors(
                    context.model_id, context.record_id)
            except RecordNotFound:
                authors = []
            finally:
                if not set(principals) ^ set(authors):
                    user_permissions -= AUTHORS_PERMISSIONS

        # Check view permission matches user permissions.
        return permissions_required.matches(user_permissions)

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()  # PRAGMA NOCOVER


class RootFactory(object):
    def __init__(self, request):
        self.db = request.db
        matchdict = request.matchdict or {}
        self.model_id = matchdict.get('model_id')
        self.record_id = matchdict.get('record_id')
        self.request = request


def build_user_principals(user, request):
    return [user]


def check_api_token(username, password, request):
    try:
        user = request.db.get_user(username)
        if user['apitoken'] == password:
            return build_user_principals(username, request)
        return []
    except UserNotFound:
        return []
