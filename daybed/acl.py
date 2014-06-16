from uuid import uuid4

import six
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.security import Authenticated, Everyone
from zope.interface import implementer

from daybed.backends.exceptions import (
    ModelNotFound, RecordNotFound, UserNotFound
)
from daybed import logger


CRUD = {'create': True,
        'read': True,
        'update': True,
        'delete': True}
C_UD = {'create': True,
        'update': True,
        'delete': True}

PERMISSION_FULL = {'definition': CRUD,
                   'records': CRUD,
                   'roles': CRUD,
                   'policy': CRUD}
PERMISSION_CREATE = {'definition': {'read': True},
                     'records': C_UD,
                     'roles': {'read': True},
                     'policy':  {'read': True}}

POLICY_READONLY = {'role:admins': PERMISSION_FULL,
                   'authors:': {'records': CRUD},
                   Authenticated: PERMISSION_CREATE,
                   Everyone: {
                       'definition': {'read': True},
                       'records': {'read': True}
                   }}
POLICY_ANONYMOUS = {Everyone: PERMISSION_FULL}
POLICY_ADMINONLY = {'group:admins': PERMISSION_FULL,
                    'role:admins': PERMISSION_FULL,
                    'authors:': {'records': CRUD},
                    Authenticated: {'definition': {'read': True}}}

VIEWS_PERMISSIONS_REQUIRED = {
    'post_model': PERMISSION_CREATE,
    'get_model':  {'definition': {'read': True},
                   'records':    {'read': True},
                   'roles':      {'read': True},
                   'policy':     {'read': True}},
    'put_model':  {'definition': C_UD,
                   'records':    C_UD,
                   'roles':      C_UD,
                   'policy':     C_UD},
    'delete_model': {'definition': {'delete': True},
                     'records':    {'delete': True},
                     'roles':      {'delete': True},
                     'policy':     {'delete': True}},

    'get_definition': {'definition': {'read': True}},

    'post_record': {'records': {'create': True}},
    'get_records': {'records': {'read': True}},
    'delete_records': {'records': {'delete': True}},

    'get_record': {'records': {'read': True}},
    'put_record': {'records': C_UD},
    'patch_record': {'records': {'update': True}},
    'delete_record': {'records': {'delete': True}}
    # XXX Add roles / policy management.
}


@implementer(IAuthorizationPolicy)
class DaybedAuthorizationPolicy(object):
    # THIS THING IS SO COOL YOU MAY WANT TO READ IT TWICE.
    # THIS THING IS SO COOL YOU MAY WANT TO READ IT TWICE.

    def permits(self, context, principals, permission):
        """Returns True or False depending if the user with the specified
        principals has access to the given permission.
        """
        allowed = 0
        permissions_required = VIEWS_PERMISSIONS_REQUIRED[permission]
        mask = get_binary_mask(permissions_required)

        if context.model_id:
            try:
                policy = context.db.get_model_policy(context.model_id)
            except ModelNotFound:
                #  In case the model doesn't exist, you have access to it.
                return True
        else:
            policy = context.db.get_policy(context.default_policy)

        for role, permissions_given in policy.items():
            permissions = get_binary_mask(permissions_given)
            if role in principals:
                allowed |= permissions

        logger.debug("(%s, %s) => %x & %x = %x" % (permission, principals,
                                                   allowed, mask,
                                                   allowed & mask))
        result = (allowed & mask) == mask
        return result

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()  # PRAGMA NOCOVER


def get_binary_mask(permission):
    """Transforms the permission as ``dict`` into a binary mask, so that it's
    possible to do boolean operations with it.

    A binary mask has four blocks of 4 bits, i.e one CRUD mask for each domain.
    Domains are definition, records, roles and policy, from left to right.

    A CRUD mask range goes from 0 (no permission) to 15 (C+R+U+D).
    """
    def singlemask(perm):
        byte = 0
        if perm.get('create'):
            byte += 8
        if perm.get('read'):
            byte += 4
        if perm.get('update'):
            byte += 2
        if perm.get('delete'):
            byte += 1
        return byte

    result = 0x0
    for i, name in enumerate(['policy', 'roles', 'records', 'definition']):
        shift = 4 * i
        mask = singlemask(permission.get(name, {}))
        result |= (mask << shift)
    return result


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
        user = request.db.add_user({'name': user, 'apitoken': token})
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
        except RecordNotFound:
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
