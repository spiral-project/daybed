from uuid import uuid4


class RandomNameGenerator(object):

    def __init__(self, config):
        pass

    def __call__(self, request):
        return str(uuid4())
