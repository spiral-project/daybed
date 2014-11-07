import os
from uuid import uuid4

import koremutake

import six


class UUID4Generator(object):

    def __init__(self, config):
        pass

    def __call__(self, key_exist=None):
        return six.text_type(uuid4()).replace('-', '')


class KoremutakeGenerator(object):

    def __init__(self, config=None):
        if config is None:
            settings = {}
        else:
            settings = config.registry.settings

        self.max_bytes = int(settings.get('id_generator.max_bytes', 4))

    def __call__(self, key_exist=None, tries=5):
        rbytes = os.urandom(self.max_bytes)
        try:
            rbytes = rbytes.encode('hex')
            random_int = int(rbytes, 16)
        except AttributeError:
            random_int = int.from_bytes(rbytes, byteorder='big')

        key = six.text_type(koremutake.encode(random_int))

        if key_exist is not None:
            if key_exist(key):
                return self.__call__(key_exist=key_exist, tries=tries - 1)
        return key
