from cornice import Service

from daybed.tokens import get_hawk_credentials

tokens = Service(name='tokens', path='/tokens', description='Tokens')

token = Service(name='token',
                path='/tokens/{token_id}',
                description='Token',
                cors_origins=('*',))


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
