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
    'read_definition', 'read_acls', 'update_definition', 'update_acls',
    'delete_model',
    'create_record',
    'read_all_records', 'update_all_records', 'delete_all_records',
    'read_my_record', 'update_my_record', 'delete_my_record'
])


def get_model_acls(token, permissions_list=PERMISSIONS_SET, acls=None):
    # - Add the token to given acls.
    # - By default give all permissions to the token
    # - You can pass existing acls if you want to add the token to some
    # permissions
    if acls is None:
        acls = defaultdict(list)
    else:
        acls = defaultdict(list, **acls)

    for perm in permissions_list:
        acls[perm].append(token)

    return acls


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
    'get_acls':       All(['read_acls']),
    'post_record':    All(['create_record']),
    'get_records':    All(['read_all_records']),
    'delete_records': All(['delete_all_records']),
    'get_record':     Any(['read_my_record', 'read_all_records']),
    'put_record':     All(['create_record',
                           Any(['update_my_record', 'update_all_records']),
                           Any(['delete_my_record', 'delete_all_records'])]),
    'patch_record':   Any(['update_my_record', 'update_all_records']),
    'delete_record':  Any(['delete_my_record', 'delete_all_records']),
    'get_tokens':     All(['manage_tokens']),
    'post_token':    Any(['create_token', 'manage_tokens']),
    'delete_token':   All(['manage_tokens']),
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
                acls = context.db.get_model_acls(context.model_id)
            except ModelNotFound:
                return True
        else:
            hasModel = False

        if hasModel:
            for acl_name, tokens in iteritems(acls):
                # If one of the principals is in the valid tokens for this,
                # permission, grant the permission.
                if set(principals).intersection(tokens):
                    token_permissions.add(acl_name)

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
        return []
    except TokenNotFound:
        return []


def invert_acls_matrix(acls_tokens):
    """Reverse from {perm: [tokens]} to {token: [perms]}."""
    tokens_acls = defaultdict(set)
    for perm, tokens in iteritems(acls_tokens):
        for token in tokens:
            tokens_acls[token].add(perm)
    return dict([(key, sorted(value)) for key, value in iteritems(tokens_acls)])
