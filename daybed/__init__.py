"""Main entry point
"""
VERSION = '0.1'

from cornice import Service
from pyramid.config import Configurator
from pyramid.renderers import JSONP
from pyramid.authentication import RemoteUserAuthenticationPolicy

from daybed.acl import (RootFactory, DaybedAuthorizationPolicy,
                        build_user_principals)


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

    # We need to scan AFTER setting the authn / authz policies
    config.scan("daybed.views")

    # backend initialisation
    backend = config.maybe_dotted(settings['daybed.backend'])
    config.registry.backend = backend(config)

    config.add_renderer('jsonp', JSONP(param_name='callback'))

    # Here, define the default users / policies etc.
    return config.make_wsgi_app()
