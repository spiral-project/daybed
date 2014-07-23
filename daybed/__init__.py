"""Main entry point
"""
import os
import logging
import pkg_resources
from collections import defaultdict


#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version

logger = logging.getLogger(__name__)

import json

import six
from cornice import Service
from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.renderers import JSONP
from pyramid.authentication import (
    AuthTktAuthenticationPolicy, BasicAuthAuthenticationPolicy
)
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.security import (
    unauthenticated_userid
)
from pyramid.settings import aslist

from pyramid_multiauth import MultiAuthenticationPolicy

from daybed.acl import (
    RootFactory, DaybedAuthorizationPolicy, build_user_principals,
    check_api_token,
)
from daybed.backends.exceptions import TokenNotFound
from daybed.views.errors import unauthorized_view
from daybed.renderers import GeoJSON


def home(request):
    try:
        token = get_token(request)
    except TokenNotFound:
        token = defaultdict(str)
    return {'token': token}


def get_token(request):
    userid = unauthenticated_userid(request)
    return request.db.get_token(userid)


def settings_expandvars(settings):
    """Expands all environment variables in a settings dictionary.
    """
    return dict((key, os.path.expandvars(value))
                for key, value in six.iteritems(settings))


def main(global_config, **settings):
    Service.cors_origins = ('*',)

    settings = settings_expandvars(settings)
    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include("cornice")
    config.include('pyramid_mako')

    # ACL management

    policies = [
        BasicAuthAuthenticationPolicy(check_api_token),
        AuthTktAuthenticationPolicy(secret, hashalg='sha512',
                                    callback=build_user_principals)
    ]
    authn_policy = MultiAuthenticationPolicy(policies)

    # Unauthorized view
    config.add_forbidden_view(unauthorized_view)

    # Authorization policy
    can_create_model = settings.get("daybed.can_create_model", "Everyone")

    if "\n" in can_create_model:
        can_create_model = can_create_model.split("\n")
    else:
        can_create_model = can_create_model.split(",")
    can_create_model = [u.strip() for u in can_create_model]

    authz_policy = DaybedAuthorizationPolicy(model_creators=can_create_model)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_token, 'token', reify=True)

    # We need to scan AFTER setting the authn / authz policies
    config.scan("daybed.views")

    # backend initialisation
    backend_class = config.maybe_dotted(settings['daybed.backend'])
    config.registry.backend = backend_class.load_from_config(config)

    def add_db_to_request(event):
        event.request.db = config.registry.backend
    config.add_subscriber(add_db_to_request, NewRequest)

    config.add_renderer('jsonp', JSONP(param_name='callback'))

    config.add_renderer('geojson', GeoJSON())
    return config.make_wsgi_app()
