class ModelCreated(object):
    def __init__(self, model_id, request):
        self.model_id = model_id
        self.request = request


class ModelUpdated(object):
    def __init__(self, model_id, request):
        self.model_id = model_id
        self.request = request


class ModelDeleted(object):
    def __init__(self, model_id, request):
        self.model_id = model_id
        self.request = request


class RecordCreated(object):
    def __init__(self, model_id, record_id, request):
        self.model_id = model_id
        self.record_id = record_id
        self.request = request


class RecordUpdated(object):
    def __init__(self, model_id, record_id, request):
        self.model_id = model_id
        self.record_id = record_id
        self.request = request


class RecordDeleted(object):
    def __init__(self, model_id, record_id, request):
        self.model_id = model_id
        self.record_id = record_id
        self.request = request
