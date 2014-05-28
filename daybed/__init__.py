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
    unauthenticated_userid,
    NO_PERMISSION_REQUIRED
)
from pyramid.settings import aslist

from pyramid_persona.utils import button, js
from pyramid_persona.views import login, logout
from pyramid_multiauth import MultiAuthenticationPolicy

from daybed.acl import (
    RootFactory, DaybedAuthorizationPolicy, build_user_principals,
    check_api_token,
    POLICY_READONLY, POLICY_ANONYMOUS, POLICY_ADMINONLY
)
from daybed.backends.exceptions import PolicyAlreadyExist, UserNotFound
from daybed.views.errors import unauthorized_view
from daybed.renderers import GeoJSON


def home(request):
    try:
        user = get_user(request)
    except UserNotFound:
        user = defaultdict(str)
    return {'user': user}


def get_user(request):
    userid = unauthenticated_userid(request)
    return request.db.get_user(userid)


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

    # Persona authentication
    secret = settings.get('persona.secret', None)

    policies = [
        BasicAuthAuthenticationPolicy(check_api_token),
        AuthTktAuthenticationPolicy(secret, hashalg='sha512',
                                    callback=build_user_principals)
    ]
    authn_policy = MultiAuthenticationPolicy(policies)

    session_factory = UnencryptedCookieSessionFactoryConfig(secret)
    config.set_session_factory(session_factory)

    verifier_factory = config.maybe_dotted(
        settings.get('persona.verifier', 'browserid.RemoteVerifier'))
    audiences = aslist(settings['persona.audiences'])
    config.registry['persona.verifier'] = verifier_factory(audiences)

    # Parameters for the request API call
    request_params = {}
    for option in ('privacyPolicy', 'siteLogo', 'siteName', 'termsOfService',
                   'backgroundColor'):
        setting_name = 'persona.%s' % option
        if setting_name in settings:
            request_params[option] = settings[setting_name]
    config.registry['persona.request_params'] = json.dumps(request_params)

    # Login and logout views.
    config.add_route('persona', '/persona')
    config.add_view(home, route_name='persona', renderer='home.mako')

    login_route = settings.get('persona.login_route', 'login')
    config.registry['persona.login_route'] = login_route
    login_path = settings.get('persona.login_path', '/login')
    config.add_route(login_route, login_path)
    config.add_view(login, route_name=login_route, check_csrf=True,
                    renderer='json', permission=NO_PERMISSION_REQUIRED)

    logout_route = settings.get('persona.logout_route', 'logout')
    config.registry['persona.logout_route'] = logout_route
    logout_path = settings.get('persona.logout_path', '/logout')
    config.add_route(logout_route, logout_path)
    config.add_view(logout, route_name=logout_route, check_csrf=True,
                    renderer='json',
                    permission=NO_PERMISSION_REQUIRED)

    config.add_request_method(button, 'persona_button', reify=True)
    config.add_request_method(js, 'persona_js', reify=True)

    # Unauthorized view
    config.add_forbidden_view(unauthorized_view)

    # Authorization policy
    authz_policy = DaybedAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)

    # We need to scan AFTER setting the authn / authz policies
    config.scan("daybed.views")

    # backend initialisation
    backend_class = config.maybe_dotted(settings['daybed.backend'])
    config.registry.backend = backend = backend_class(config)

    def add_db_to_request(event):
        event.request.db = config.registry.backend.db()
    config.add_subscriber(add_db_to_request, NewRequest)

    config.add_renderer('jsonp', JSONP(param_name='callback'))

    # Here, define the default users / policies etc.
    database = backend.db()
    for name, policy in [('read-only', POLICY_READONLY),
                         ('anonymous', POLICY_ANONYMOUS),
                         ('admin-only', POLICY_ADMINONLY)]:
        try:
            database.set_policy(name, policy)
        except PolicyAlreadyExist:
            pass

    config.registry.default_policy = settings.get('daybed.default_policy',
                                                  'read-only')

    config.add_renderer('geojson', GeoJSON())
    return config.make_wsgi_app()
