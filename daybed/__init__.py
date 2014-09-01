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
    RootFactory, DaybedAuthorizationPolicy, get_credentials, check_credentials
)
from daybed.views.errors import forbidden_view
from daybed.renderers import GeoJSON
from daybed import indexer, events


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
        BasicAuthAuthenticationPolicy(check_credentials),
        HawkAuthenticationPolicy(decode_hawk_id=get_credentials),
    ]
    authn_policy = MultiAuthenticationPolicy(policies)

    # Unauthorized view
    config.add_forbidden_view(forbidden_view)

    # Global permissions
    model_creators = settings.get("daybed.can_create_model", "Everyone")
    token_creators = settings.get("daybed.can_create_token", "Everyone")
    token_managers = settings.get("daybed.can_manage_token", None)

    authz_policy = DaybedAuthorizationPolicy(
        model_creators=build_list(model_creators),
        token_creators=build_list(token_creators),
        token_managers=build_list(token_managers),
    )
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    # We need to scan AFTER setting the authn / authz policies
    config.scan("daybed.views")

    # Attach the token to the request, coming from Pyramid as userid
    def get_credentials_id(request):
        try:
            credentials_id, _ = get_credentials(request,
                                                request.authenticated_userid)
            return credentials_id
        except ValueError:
            return None

    config.add_request_method(get_credentials_id, 'credentials_id', reify=True)

    # Events

    # Helper for notifying events
    def notify(request, event, *args):
        klass = config.maybe_dotted('daybed.events.' + event)
        event = klass(*(args + (request,)))
        request.registry.notify(event)

    config.add_request_method(notify, 'notify')

    # Backend

    # backend initialisation
    backend_class = config.maybe_dotted(settings['daybed.backend'])
    config.registry.backend = backend_class.load_from_config(config)

    # Indexing

    # Connect client to hosts in conf
    index_hosts = build_list(settings.get('elasticsearch.hosts'))
    indices_prefix = settings.get('elasticsearch.indices_prefix', 'daybed_')
    config.registry.index = index = indexer.ElasticSearchIndexer(
        index_hosts, indices_prefix
    )

    # Suscribe index methods to API events
    config.add_subscriber(index.on_model_created, events.ModelCreated)
    config.add_subscriber(index.on_model_updated, events.ModelUpdated)
    config.add_subscriber(index.on_model_deleted, events.ModelDeleted)
    config.add_subscriber(index.on_record_created, events.RecordCreated)
    config.add_subscriber(index.on_record_updated, events.RecordUpdated)
    config.add_subscriber(index.on_record_deleted, events.RecordDeleted)

    # Renderers

    # Force default accept header to JSON
    def add_default_accept(event):
        if "Accept" not in event.request.headers:
            event.request.headers["Accept"] = "application/json"

    config.add_subscriber(add_default_accept, NewRequest)

    # JSONP
    config.add_renderer('jsonp', JSONP(param_name='callback'))

    # Geographic data renderer
    config.add_renderer('geojson', GeoJSON())

    # Requests attachments

    def attach_objects_to_request(event):
        event.request.db = config.registry.backend
        event.request.index = config.registry.index
        http_scheme = event.request.registry.settings.get('daybed.http_scheme')
        if http_scheme:
            event.request.scheme = http_scheme

    config.add_subscriber(attach_objects_to_request, NewRequest)

    # Plugins

    try:
        config.include("daybed_browserid")
    except ImportError:
        pass

    return config.make_wsgi_app()
