import sys
import six


def to_unicode(x, charset=sys.getdefaultencoding(), errors='strict',
               allow_none_charset=False):
    if x is None:
        return None
    if not isinstance(x, bytes):
        return six.text_type(x)
    if charset is None and allow_none_charset:
        return x
    return x.decode(charset, errors)
