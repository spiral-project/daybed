from cornice import Service

from daybed.tokens import get_hawk_credentials

tokens = Service(name='tokens', path='/tokens', description='Tokens',
                 renderer="jsonp", cors_origins=('*',))


token = Service(name='token',
                path='/tokens/{token_id}',
                description='Token',
                renderer="jsonp",
                cors_origins=('*',))


@tokens.post(permission='post_token')
def post_tokens(request):
    """Creates a new token and store it"""
    session_token, credentials = get_hawk_credentials()
    request.db.add_token(credentials["id"], credentials["key"])

    request.response.status = "201 Created"
    return {
        'sessionToken': session_token,
        'credentials': credentials
    }
