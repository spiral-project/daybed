from pyramid.security import Everyone
from pyramid.httpexceptions import HTTPUnauthorized, HTTPForbidden

from cornice.cors import ensure_origin


def forbidden_view(request):
    if not request.credentials_id or request.credentials_id == Everyone:
        response = HTTPUnauthorized()
    else:
        response = HTTPForbidden()

    # We need to re-apply the CORS checks done by Cornice, since we're
    # recreating the response from scratch.
    services = request.registry.cornice_services
    pattern = request.matched_route.pattern
    service = services.get(pattern, None)

    request.info['cors_checked'] = False
    resp = ensure_origin(service, request, response)
    return resp
