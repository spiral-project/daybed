from .database import Database


class MemoryBackend(object):
    def db(self):
        return Database(self.__db, self._generate_id)

    def __init__(self, config):
        # model id generator
        settings = config.registry.settings
        generator = config.maybe_dotted(settings['daybed.id_generator'])
        self._generate_id = generator(config)

        self.__init_db()
        self._db = self.db()

    def delete_db(self):
        self.__db.clear()
        self.__init_db()

    def __init_db(self):
        self.__db = {
            'models': {},
            'data': {},
            'users': {},
            'policies': {}
        }
