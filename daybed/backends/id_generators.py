from uuid import uuid4

import six


class UUID4Generator(object):

    def __init__(self, config):
        pass

    def __call__(self, request=None):
        return six.text_type(uuid4()).replace('-', '')
