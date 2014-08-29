from cornice import Service

from daybed.tokens import get_hawk_credentials
from daybed.views.errors import forbidden_view

tokens = Service(name='tokens', path='/tokens', description='Tokens')
token = Service(name='token', path='/token', description='Token')


@tokens.post(permission='post_token')
def post_tokens(request):
    """Creates a new token and store it"""
    token, credentials = get_hawk_credentials()
    request.db.store_credentials(token, credentials)

    request.response.status = "201 Created"

    return {
        'token': token,
        'credentials': credentials
    }


@token.get()
def get_token(request):
    if request.credentials_id:
        token = request.db.get_token(request.credentials_id)
        _, credentials = get_hawk_credentials(token)

        return {
            'token': token,
            'credentials': credentials
        }
    else:
        return forbidden_view(request)
