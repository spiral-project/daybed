# -*- coding: utf-8 -*-
import codecs
import hashlib
import hmac as python_hmac
import math
import os
from six import text_type
from six.moves import xrange


def hmac_digest(key, content):
    return python_hmac.new(
        key.encode("ascii"),
        content.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def get_hawk_credentials(token=None):
    if token is None:
        token = os.urandom(32)
    else:
        token = codecs.decode(token, "hex_codec")

    # sessionToken protocol HKDF keyInfo.
    keyInfo = 'identity.mozilla.com/picl/v1/sessionToken'
    keyMaterial = HKDF(token, "", keyInfo, 32*2)

    token = codecs.encode(token, "hex_codec").decode("utf-8")

    return token, {
        'id': codecs.encode(keyMaterial[:32], "hex_codec").decode("utf-8"),
        'key': codecs.encode(keyMaterial[32:64], "hex_codec").decode("utf-8"),
        'algorithm': 'sha256'
    }


def HKDF_extract(salt, IKM, hashmod=hashlib.sha256):
    """HKDF-Extract; see RFC-5869 for the details."""
    if salt is None:
        salt = b"\x00" * hashmod().digest_size
    if isinstance(salt, text_type):
        salt = salt.encode("utf-8")
    return python_hmac.new(salt, IKM, hashmod).digest()


def HKDF_expand(PRK, info, L, hashmod=hashlib.sha256):
    """HKDF-Expand; see RFC-5869 for the details."""
    if isinstance(info, text_type):
        info = info.encode("utf-8")
    digest_size = hashmod().digest_size
    N = int(math.ceil(L * 1.0 / digest_size))
    assert N <= 255
    T = b""
    output = []
    for i in xrange(1, N + 1):
        data = T + info + chr(i).encode("utf-8")
        T = python_hmac.new(PRK, data, hashmod).digest()
        output.append(T)
    return b"".join(output)[:L]


def HKDF(secret, salt, info, size, hashmod=hashlib.sha256):
    """HKDF-extract-and-expand as a single function."""
    PRK = HKDF_extract(salt, secret, hashmod)
    return HKDF_expand(PRK, info, size, hashmod)
