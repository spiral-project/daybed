from pyramid.response import Response


def unauthorized_view(request):
    return Response('{"error": "401 Unauthorized",'
                    ' "msg": "You must login to access this page."}',
                    status='401 Unauthorized', content_type='application/json')
