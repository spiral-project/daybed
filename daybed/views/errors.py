from pyramid.response import Response
from pyramid.security import Everyone

from cornice.cors import ensure_origin


def forbidden_view(request):
    if not request.credentials_id or request.credentials_id == Everyone:
        resp = Response(
            '{"error": "401 Unauthorized",'
            ' "msg": "You must be logged-in to access this page."}',
            status='401 Unauthorized', content_type='application/json')
    else:
        resp = Response(
            '{"error": "403 Forbidden",'
            ' "credentials_id": "%s", "msg": "Access to this resource is '
            'Forbidden."}' % request.credentials_id, status='403 Forbidden',
            content_type='application/json')

    # We need to re-apply the CORS checks done by Cornice, since we're
    # recreating the response from scratch.
    services = request.registry.cornice_services
    pattern = request.matched_route.pattern
    service = services.get(pattern, None)

    request.info['cors_checked'] = False
    resp = ensure_origin(service, request, resp)
    return resp
