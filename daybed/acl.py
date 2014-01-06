import six
from uuid import uuid4
from pyramid.interfaces import IAuthorizationPolicy
from zope.interface import implementer

from daybed.backends.exceptions import (
    ModelNotFound, DataItemNotFound, UserNotFound
)
from daybed.log import logger


@implementer(IAuthorizationPolicy)
class DaybedAuthorizationPolicy(object):
    # THIS THING IS SO COOL YOU MAY WANT TO READ IT TWICE.
    # THIS THING IS SO COOL YOU MAY WANT TO READ IT TWICE.

    def permits(self, context, principals, permission):
        """Returns True or False depending if the user with the specified
        principals has access to the given permission.
        """
        allowed = 0
        mask = permission_mask(permission)

        if context.model_id:
            try:
                policy = context.db.get_model_policy(context.model_id)
            except ModelNotFound:
                #  In case the model doesn't exist, you have access to it.
                return True
        else:
            policy = context.db.get_policy(context.default_policy)

        for role, permissions in policy.items():
            if role in principals:
                allowed |= permissions

        logger.debug("(%s, %s) => %x & %x = %x" % (permission, principals,
                                                   allowed, mask,
                                                   allowed & mask))
        result = allowed & mask == mask
        return result

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()  # PRAGMA NOCOVER


def permission_mask(permission):
    """Returns the permission mask associated with a permission, so that it's
    possible to do boolean operations with them.

    Permissions are defined with the format {privilege}_{resource}.
    """
    # As a note, here are the permissions, for a "CRUD":
    # Create = 8
    # Read   = 4
    # Update = 2
    # Delete = 1

    # The order matters and is "Definition, Data, Users, Policy".

    mapping = {
        'post_model': 0x8888,        # C on everything
        'get_model': 0x4444,         # R on everything
        'put_model': 0xBBBB,         # C+U+D on everything
        'delete_model': 0x1111,      # D on everything

        'get_definition': 0x4000,

        'post_data': 0x0800,         # C
        'get_data': 0x0400,          # R
        'put_data': 0x0B00,          # C+U+D
        'delete_data': 0x0100,       # D

        'get_record': 0x0400,        # R
        'put_record': 0x0B00,        # C+U+D
        'patch_record': 0x0200,      # U
        'delete_record': 0x0100,     # D
    }
    # XXX Add users / policy management.
    return mapping[permission]


class RootFactory(object):
    def __init__(self, request):
        self.db = request.db
        self.default_policy = request.registry.default_policy
        matchdict = request.matchdict or {}
        self.model_id = matchdict.get('model_id')
        self.record_id = matchdict.get('record_id')
        self.request = request


def build_user_principals(user, request):
    """Returns the principals for an user.

    On the returned principals, there can be groups, roles and authors.
    Each of these special groups are prefixed with '<group>:<name>', e.g.
    'group:readers', 'role:curator' and 'author:'.
    """
    model_id = request.matchdict.get('model_id')
    record_id = request.matchdict.get('record_id')

    try:
        groups = [u'group:%s' % g for g in request.db.get_groups(user)]
    except UserNotFound:
        token = six.text_type(uuid4())
        user = request.db.add_user({'name': user, 'api-token': token})
        groups = user['groups']
    principals = set(groups)

    if model_id is not None:
        try:
            roles = request.db.get_roles(model_id)
        except ModelNotFound:
            roles = {}

        for role_name, accredited in roles.items():
            for acc in accredited:
                if acc.startswith('group:'):
                    for group in groups:
                        if group == acc:
                            principals.add(u'role:%s' % role_name)
                else:
                    if user == acc:
                        principals.add(u'role:%s' % role_name)

    if record_id is not None:
        try:
            authors = request.db.get_record_authors(model_id, record_id)
        except DataItemNotFound:
            pass
        else:
            if user in authors:
                principals.add('authors:')

    return principals


def check_api_token(username, password, request):
    try:
        user = request.db.get_user(username)
    except UserNotFound:
        # We create the user if it doesn't exists yet.
        user = {'name': username, 'apitoken': password}
        user = request.db.add_user(user)
    if user['apitoken'] == password:
        return build_user_principals(username, request)
