from pyramid.events import NewRequest

from .database import Database


class MemoryBackend(object):
    def db(self):
        return Database(self._db, self._generate_id)

    def __init__(self, config):
        settings = config.registry.settings

        self._db = {
            'models': {},
            'data': {}
        }

        # model id generator
        generator = config.maybe_dotted(settings['daybed.id_generator'])
        self._generate_id = generator(config)

        config.add_subscriber(self.add_db_to_request, NewRequest)

    def delete_db(self):
        self._db.clear()
        self._db = {
            'models': {},
            'data': {}
        }

    def add_db_to_request(self, event):
        event.request.db = self.db
