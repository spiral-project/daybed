# -*- coding: utf-8 -*-
import binascii
import hashlib
import hmac as python_hmac
import math
from six import text_type
from six.moves import xrange


def hmac(data, secret, hashmod=hashlib.sha256):
    if isinstance(secret, text_type):
        secret = secret.encode("utf-8")
    if isinstance(data, text_type):
        data = data.encode("utf-8")

    return binascii.hexlify(python_hmac.new(
        secret, data, hashmod
    ).digest())


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
