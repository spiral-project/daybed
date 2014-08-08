# -*- coding: utf-8 -*-
from collections import defaultdict
from six import iteritems
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.security import Authenticated, Everyone
from zope.interface import implementer

from daybed.backends.exceptions import (
    ModelNotFound, RecordNotFound, TokenNotFound
)
from daybed import logger

PERMISSIONS_SET = set([
    'read_definition', 'update_permissions',
    'read_permissions', 'update_definition',
    'delete_model',
    'create_record',
    'read_all_records', 'update_all_records', 'delete_all_records',
    'read_own_records', 'update_own_records', 'delete_own_records'
])


def get_model_permissions(token, all_perms=PERMISSIONS_SET, permissions=None):
    # - Add the token to given permissions.
    # - By default give all permissions to the token
    # - You can pass existing permissions if you want to add the token to some
    # permissions
    if permissions is None:
        permissions = defaultdict(list)
    else:
        permissions = defaultdict(list, **permissions)

    for perm in all_perms:
        permissions[perm].append(token)

    return permissions


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


AUTHORS_PERMISSIONS = set(['update_own_records', 'delete_own_records',
                           'read_own_records'])

VIEWS_PERMISSIONS_REQUIRED = {
    'post_model':      All(['create_model']),
    'get_model':       All(['read_definition', 'read_permissions',
                           Any(['read_all_records', 'read_own_recordss'])]),
    'put_model':       All(['create_model', 'update_definition',
                            'update_permissions', 'delete_model']),
    'delete_model':    All(['delete_model', 'delete_all_records']),
    'get_definition':  All(['read_definition']),
    'get_permissions': All(['read_permissions']),
    'put_permissions': All(['update_permissions']),
    'post_record':     All(['create_record']),
    'get_records':     Any(['read_all_records', 'read_own_records']),
    'delete_records':  All(['delete_all_records']),
    'get_record':      Any(['read_own_records', 'read_all_records']),
    'put_record':      All(['create_record',
                           Any(['update_own_records', 'update_all_records']),
                           Any(['delete_own_records', 'delete_all_records'])]),
    'patch_record':    Any(['update_own_records', 'update_all_records']),
    'delete_record':   Any(['delete_own_records', 'delete_all_records']),
    'get_tokens':      All(['manage_tokens']),
    'post_token':      Any(['create_token', 'manage_tokens']),
    'delete_token':    All(['manage_tokens']),
}


@implementer(IAuthorizationPolicy)
class DaybedAuthorizationPolicy(object):

    def __init__(self, model_creators="Everyone", token_creators="Everyone",
                 token_managers=None):
        self.model_creators = self._handle_pyramid_constants(model_creators)
        self.token_creators = self._handle_pyramid_constants(token_creators)
        self.token_managers = self._handle_pyramid_constants(token_managers)

    def _handle_pyramid_constants(self, creators):
        if not creators:
            return set()

        creators = set(creators)

        # Handle Pyramid constants.
        if "Authenticated" in creators:
            creators.remove("Authenticated")
            creators.add(Authenticated)

        if "Everyone" in creators:
            creators.remove("Everyone")
            creators.add(Everyone)

        return creators

    def add_conf_rights(self, creators, principals, permissions, perm):
        if creators.intersection(principals) != set():
            permissions.add(perm)

    def permits(self, context, principals, permission):
        """Returns True or False depending if the token with the specified
        principals has access to the given permission.
        """
        permissions_required = VIEWS_PERMISSIONS_REQUIRED[permission]

        token_permissions = set()

        self.add_conf_rights(self.model_creators, principals,
                             token_permissions, "create_model")
        self.add_conf_rights(self.token_creators, principals,
                             token_permissions, "create_token")
        self.add_conf_rights(self.token_managers, principals,
                             token_permissions, "manage_token")

        hasModel = True

        if context.model_id:
            try:
                perms = context.db.get_model_permissions(context.model_id)
            except ModelNotFound:
                return True
        else:
            hasModel = False

        if hasModel:
            for perm_name, tokens in iteritems(perms):
                # If one of the principals is in the valid tokens for this,
                # permission, grant the permission.
                if set(principals).intersection(tokens):
                    token_permissions.add(perm_name)

            logger.debug("token permissions: %s", token_permissions)

            if context.record_id is not None:
                try:
                    authors = context.db.get_record_authors(
                        context.model_id, context.record_id)
                except RecordNotFound:
                    authors = []
                finally:
                    if not set(principals).intersection(authors):
                        token_permissions -= AUTHORS_PERMISSIONS

        # Expose permissions and principals for in_view checks
        context.request.permissions = token_permissions
        context.request.principals = principals

        # Check view permission matches token permissions.
        return permissions_required.matches(token_permissions)

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()  # PRAGMA NOCOVER


class RootFactory(object):
    def __init__(self, request):
        self.db = request.db
        matchdict = request.matchdict or {}
        self.model_id = matchdict.get('model_id')
        self.record_id = matchdict.get('record_id')
        self.request = request


def build_user_principals(token, request):
    return [token]


def check_api_token(tokenId, tokenKey, request):
    try:
        secret = request.db.get_token(tokenId)
        if secret == tokenKey:
            return build_user_principals(tokenId, request)
        request.token = None
        request.principals = [Everyone]
        return []
    except TokenNotFound:
        request.token = None
        request.principals = [Everyone]
        return []


def dict_set2list(dict_set):
    return dict([(key, sorted(value))
                 for key, value in iteritems(dict_set)])


def dict_list2set(dict_list):
    return dict([(key, set(value))
                 for key, value in iteritems(dict_list)])


def invert_permissions_matrix(permissions_tokens):
    """Reverse from {perm: [tokens]} to {token: [perms]}."""
    tokens_permissions = defaultdict(set)
    for perm, tokens in iteritems(permissions_tokens):
        for token in tokens:
            tokens_permissions[token].add(perm)
    return dict_set2list(tokens_permissions)
