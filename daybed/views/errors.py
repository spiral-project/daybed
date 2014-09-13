from pyramid.security import Everyone
from pyramid.httpexceptions import HTTPUnauthorized, HTTPForbidden

from cornice.cors import ensure_origin


def forbidden_view(request):
    if not request.credentials_id or request.credentials_id == Everyone:
        response = HTTPUnauthorized()
    else:
        response = HTTPForbidden()

    services = request.registry.cornice_services
    pattern = request.matched_route.pattern
    service = services.get(pattern, None)

    resp = ensure_origin(service, request, response)
    return resp
