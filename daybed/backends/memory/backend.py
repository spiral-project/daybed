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

    def delete_db(self):
        self._db.clear()
        self._db = {
            'models': {},
            'data': {}
        }
