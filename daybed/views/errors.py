from pyramid.response import Response
from pyramid.security import Everyone


def forbidden_view(request):
    if not request.credentials_id or request.credentials_id == Everyone:
        return Response(
            '{"error": "401 Unauthorized",'
            ' "msg": "You must be logged-in to access this page."}',
            status='401 Unauthorized', content_type='application/json')
    return Response(
        '{"error": "403 Forbidden",'
        ' "credentials_id": "%s", "msg": "Access to this resource is '
        'Forbidden."}' % request.credentials_id, status='403 Forbidden',
        content_type='application/json')
