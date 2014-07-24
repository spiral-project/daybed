import os
import codecs
from cornice import Service

from daybed.hkdf import HKDF, hmac

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
    session_token = os.urandom(32)
    keyInfo = 'identity.mozilla.com/picl/v1/sessionToken'
    keyMaterial = HKDF(session_token, "", keyInfo, 32*2)

    credentials = {
        'id': codecs.encode(keyMaterial[:32], "hex_codec").decode("utf-8"),
        'key': codecs.encode(keyMaterial[32:64], "hex_codec").decode("utf-8"),
        'algorithm': 'sha256'
    }

    hmacId = hmac(credentials["id"], request.hawkHmacKey)
    request.db.add_token(hmacId, credentials["key"])

    session_token = codecs.encode(session_token, "hex_codec").decode("utf-8")

    return {
        'sessionToken': session_token,
        'credentials': credentials
    }
