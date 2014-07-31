from pyramid.response import Response
from pyramid.security import Everyone


def forbidden_view(request):
    if not request.token or request.token == Everyone:
        return Response(
            '{"error": "401 Unauthorized",'
            ' "msg": "You must be logged-in to access this page."}',
            status='401 Unauthorized', content_type='application/json')
    return Response(
        '{"error": "403 Forbidden",'
        ' "token": "%s", '
        ' "msg": "Access to this resource is Forbidden."}' % request.token,
        status='403 Forbidden', content_type='application/json')
