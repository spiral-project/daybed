from cornice import Service

from daybed.backends.exceptions import CredentialsAlreadyExist
from daybed.tokens import get_hawk_credentials, hmac_digest
from daybed.views.errors import forbidden_view

tokens = Service(name='tokens', path='/tokens', description='Tokens')
token = Service(name='token', path='/token', description='Token')


@tokens.post(permission='post_token')
def post_tokens(request):
    """Creates a new token and store it"""

    # If we have an authorization header with the Basic or Token realm
    # Use it to derive the key
    session_token = None
    if request.authorization and \
       request.authorization[0] in ["Basic", "Token"]:
        session_token = hmac_digest(request.registry.tokenHmacKey,
                                    "%s %s" % request.authorization[:2])
    token, credentials = get_hawk_credentials(session_token)

    try:
        request.db.store_credentials(token, credentials)
    except CredentialsAlreadyExist:
        request.response.status = "200 OK"
    else:
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
