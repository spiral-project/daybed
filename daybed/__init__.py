"""Main entry point
"""
import os
import logging
import pkg_resources


#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version

logger = logging.getLogger(__name__)

import six
from cornice import Service
from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.renderers import JSONP
from pyramid.authentication import BasicAuthAuthenticationPolicy

from pyramid_hawkauth import HawkAuthenticationPolicy
from pyramid_multiauth import MultiAuthenticationPolicy

from daybed.permissions import (
    RootFactory, DaybedAuthorizationPolicy, check_api_token,
)
from daybed.views.errors import forbidden_view
from daybed.renderers import GeoJSON
from daybed.backends.exceptions import TokenNotFound
from daybed.indexer import DaybedIndexer


def get_hawk_id(request, tokenid):
    try:
        return tokenid, request.db.get_token(tokenid)
    except TokenNotFound:
        raise ValueError


def settings_expandvars(settings):
    """Expands all environment variables in a settings dictionary.
    """
    return dict((key, os.path.expandvars(value))
                for key, value in six.iteritems(settings))


def build_list(variable):
    if not variable:
        return []
    elif "\n" in variable:
        variable = variable.split("\n")
    else:
        variable = variable.split(",")
    return [v.strip() for v in variable]


def main(global_config, **settings):
    Service.cors_origins = ('*',)

    settings = settings_expandvars(settings)
    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include("cornice")

    # Permission management

    policies = [
        BasicAuthAuthenticationPolicy(check_api_token),
        HawkAuthenticationPolicy(decode_hawk_id=get_hawk_id),
    ]
    authn_policy = MultiAuthenticationPolicy(policies)

    # Unauthorized view
    config.add_forbidden_view(forbidden_view)

    # Authorization policy
    authz_policy = DaybedAuthorizationPolicy(
        model_creators=build_list(
            settings.get("daybed.can_create_model", "Everyone")),
        token_creators=build_list(
            settings.get("daybed.can_create_token", "Everyone")),
        token_managers=build_list(
            settings.get("daybed.can_manage_token", None)),
    )
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    def get_token(request):
        return request.authenticated_userid

    config.add_request_method(get_token, 'token', reify=True)

    # We need to scan AFTER setting the authn / authz policies
    config.scan("daybed.views")

    # backend initialisation
    backend_class = config.maybe_dotted(settings['daybed.backend'])
    config.registry.backend = backend_class.load_from_config(config)

    def add_db_to_request(event):
        event.request.db = config.registry.backend

    config.add_subscriber(add_db_to_request, NewRequest)

    # index initialization
    index_hosts = build_list(settings.get('index.host', 'localhost:9200'))
    config.registry.index = DaybedIndexer(config, index_hosts)

    def add_index_to_request(event):
        event.request.index = config.registry.index

    config.add_subscriber(add_index_to_request, NewRequest)

    # Renderers initialization
    def add_default_accept(event):
        # If the user doesn't give us an Accept header, force the use
        # of the JSON renderer
        if "Accept" not in event.request.headers:
            event.request.headers["Accept"] = "application/json"

    config.add_subscriber(add_default_accept, NewRequest)

    config.add_renderer('jsonp', JSONP(param_name='callback'))
    config.add_renderer('geojson', GeoJSON())

    return config.make_wsgi_app()
