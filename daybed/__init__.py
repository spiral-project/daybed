"""Main entry point
"""
VERSION = '0.1'

from cornice import Service
from pyramid.config import Configurator
from pyramid.renderers import JSONP
from pyramid.authentication import RemoteUserAuthenticationPolicy

from daybed.acl import (RootFactory, DaybedAuthorizationPolicy,
                        build_user_principals)
from daybed.backends.exceptions import PolicyAlreadyExist
from pyramid.security import unauthenticated_userid


def get_user(request):
    userid = unauthenticated_userid(request)
    if userid is not None:
        return request.db.get_user(userid)


def main(global_config, **settings):
    Service.cors_origins = ('*',)

    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include("cornice")

    # ACL management
    authn_policy = RemoteUserAuthenticationPolicy(
        'HTTP_REMOTE_USER',
        callback=build_user_principals)

    authz_policy = DaybedAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)

    # We need to scan AFTER setting the authn / authz policies
    config.scan("daybed.views")

    # backend initialisation
    backend_class = config.maybe_dotted(settings['daybed.backend'])
    backend = backend_class(config)
    config.registry.backend = backend

    config.add_renderer('jsonp', JSONP(param_name='callback'))

    # Here, define the default users / policies etc.
    try:
        backend._db.set_policy('read-only', {'role:admins': 0xFFFF,
                                             'others:': 0x4400})
    except PolicyAlreadyExist:
        pass
    config.registry.default_policy = 'read-only'

    return config.make_wsgi_app()
