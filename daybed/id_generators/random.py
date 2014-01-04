import six
from uuid import uuid4


class UUID4Generator(object):

    def __init__(self, config):
        pass

    def __call__(self, request=None):
        return six.text_type(uuid4()).replace('-', '')
