# -*- coding: utf-8 -*-
from collections import defaultdict
from six import iteritems
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.security import Authenticated, Everyone
from zope.interface import implementer

from daybed.backends import exceptions as backend_exceptions
from daybed import logger


PERMISSIONS_SET = set([
    'read_definition', 'update_permissions',
    'read_permissions', 'update_definition',
    'delete_model',
    'create_record',
    'read_all_records', 'update_all_records', 'delete_all_records',
    'read_own_records', 'update_own_records', 'delete_own_records'
])


def default_model_permissions(credentials_id):
    """ Give all permissions to the model creator.
    Permissions of models created by anonymous (i.e. ``Everyone``)
    cannot be changed.
    """
    permissions = defaultdict(list)
    for perm in PERMISSIONS_SET:
        permissions[perm].append(credentials_id)

    if credentials_id == Everyone:
        permissions.pop('update_permissions')

    return permissions


def merge_permissions(original, specified):
    """ Merge permissions together, and handle the ``ALL`` shortcut.
    """
    permissions = dict_list2set(original)

    def _add(perm, identifier):
        permissions.setdefault(perm, set()).add(identifier)

    def _discard(perm, identifier):
        permissions.setdefault(perm, set()).discard(identifier)

    for credentials_id, perms in iteritems(specified):
        # Handle remove all
        if '-all' in [perm.lower() for perm in perms]:
            for perm in PERMISSIONS_SET:
                _discard(perm, credentials_id)

        # Handle add all
        elif 'all' in [perm.lstrip('+').lower() for perm in perms]:
            for perm in PERMISSIONS_SET:
                _add(perm, credentials_id)

        # Handle add/remove perms list
        else:
            for perm in [perm.lower() for perm in perms]:
                if perm.startswith('-'):
                    _discard(perm.lstrip('-'), credentials_id)
                else:
                    _add(perm.lstrip('+'), credentials_id)

    return dict_set2list(permissions)


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
    'get_models':      All(),
    'post_model':      All(['create_model']),
    'get_model':       All(['read_definition', 'read_permissions',
                           Any(['read_all_records', 'read_own_records'])]),
    'put_model':       All(['create_model', 'update_definition',
                            'update_permissions', 'delete_model']),
    'delete_model':    All(['delete_model', 'delete_all_records']),
    'get_definition':  All(['read_definition']),
    'get_permissions': All(['read_permissions']),
    'put_permissions': All(['update_permissions']),
    'post_record':     All(['create_record']),
    'get_all_records': All(['read_all_records']),
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

    def permits(self, context, principals, permission):
        """Returns True or False depending if the token with the specified
        principals has access to the given permission.
        """
        principals = set(principals)
        permissions_required = VIEWS_PERMISSIONS_REQUIRED[permission]
        current_permissions = set()

        if principals.intersection(self.model_creators):
            current_permissions.add("create_model")

        if principals.intersection(self.token_creators):
            current_permissions.add("create_token")

        if principals.intersection(self.token_managers):
            current_permissions.add("manage_token")

        model_id = context.model_id
        if model_id is not None:
            try:
                model_permissions = context.db.get_model_permissions(model_id)
            except backend_exceptions.ModelNotFound:
                model_permissions = {}
                if permission != 'post_model':
                    # Prevent unauthorized error to shadow 404 responses
                    return True
            finally:
                for perm_name, credentials_ids in iteritems(model_permissions):
                    # If one of the principals is in the valid credentials_ids
                    # for this permission, grant the permission.
                    if principals.intersection(credentials_ids):
                        current_permissions.add(perm_name)

        # Remove author's permissions if a record is involved, and if it
        # does not belong to the token.
        record_id = context.record_id
        if record_id is not None:
            try:
                authors = context.db.get_record_authors(model_id, record_id)
            except backend_exceptions.RecordNotFound:
                authors = []
            finally:
                if not principals.intersection(authors):
                    current_permissions -= AUTHORS_PERMISSIONS

        logger.debug("Current permissions: %s", current_permissions)

        # Expose permissions and principals for in_view checks
        context.request.permissions = current_permissions
        context.request.principals = principals

        # Check view permission matches token permissions.
        return permissions_required.matches(current_permissions)

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()  # PRAGMA NOCOVER


class RootFactory(object):
    def __init__(self, request):
        self.db = request.db
        matchdict = request.matchdict or {}
        self.model_id = matchdict.get('model_id')
        self.record_id = matchdict.get('record_id')
        self.request = request


def get_credentials(request, credentials_id):
    """ Retrieve credentials from backend.
    """
    if credentials_id is Everyone:
        return Everyone, None
    try:
        stored_key = request.db.get_credentials_key(credentials_id)
    except backend_exceptions.CredentialsNotFound:
        raise ValueError
    return credentials_id, stored_key


def check_credentials(credentials_id, credentials_key, request):
    """ Retrieve credentials and check value of secret key.
    (Used by BasicAuth policy).
    """
    try:
        _, stored_key = get_credentials(request, credentials_id)
        if stored_key == credentials_key:
            return [credentials_id]
    except ValueError:
        pass
    request.principals = [Everyone]
    return []


def dict_set2list(dict_set):
    return dict([(key, sorted(value))
                 for key, value in iteritems(dict_set)])


def dict_list2set(dict_list):
    return dict([(key, set(value))
                 for key, value in iteritems(dict_list)])


def invert_permissions_matrix(permissions_credentials_ids):
    """Reverse from {perm: [credentials_ids]} to {credentials_id: [perms]}."""
    credentials_ids_permissions = defaultdict(set)
    for perm, credentials_ids in iteritems(permissions_credentials_ids):
        for credentials_id in credentials_ids:
            credentials_ids_permissions[credentials_id].add(perm)
    return dict_set2list(credentials_ids_permissions)
