from sqlalchemy import create_engine
from sqlalchemy_utils.functions import database_exists
from sqlalchemy.orm import sessionmaker

from frosti.core import ServiceProvider, ServiceConsumer
from frosti.core.orm import OrmConfig, Base

DB_URL_TEMPLATE = 'postgresql://frosti:frosti@localhost/template1'
DB_URL_RUN = 'postgresql://frosti:frosti@localhost/frosti'
DB_URL_TEST = 'postgresql://frosti:frosti@localhost/frosti_test'
DB_VERSION = 'v1.2'


class OrmManagementService(ServiceConsumer):

    def __init__(self, isTestInstance: bool = False):
        url = DB_URL_TEST if isTestInstance else DB_URL_RUN
        if not database_exists(url):
            name = 'frosti_test' if isTestInstance else 'frosti'
            engine = create_engine(
                DB_URL_TEMPLATE, isolation_level='AUTOCOMMIT')
            session = sessionmaker(bind=engine)()
            session.execute(f'CREATE DATABASE {name}')

        self.__engine = create_engine(url, echo=False)
        self.__session = sessionmaker(bind=self.__engine)()
        self.__connection = self.__engine.connect()

    def setServiceProvider(self, provider: ServiceProvider):
        super().setServiceProvider(provider)

        Base.metadata.create_all(self.__engine)

        # Ensure the DB version agrees with the code version.  If for some
        # reason the database doesn't have a version, assume it's current and
        # then set it properly
        dbVersion = None
        for configEntry in self.__session.query(OrmConfig). \
                filter(OrmConfig.name == 'db.version'):
            dbVersion = configEntry.value
        if dbVersion is None:
            configEntry = OrmConfig()
            configEntry.name = 'db.version'
            configEntry.value = DB_VERSION
            dbVersion = DB_VERSION
            self.__session.add(configEntry)
            self.__session.commit()

        if DB_VERSION != dbVersion:
            raise RuntimeError('Database needs upgraded')

    @property
    def session(self):
        ''' Returns the currently active SqlAlchemy session '''
        return self.__session

    def getConfigString(self, name: str, default: str = None):
        ''' Returns a configuration value for a given name '''
        for configEntry in self.__session.query(OrmConfig). \
                filter(OrmConfig.name == name):
            return configEntry.value

        if default is not None:
            return default

        raise RuntimeError(f'Config key "{name}" is not defined')

    def getConfigInt(self, name: str, default: str = None):
        ''' Convenience method for getting a configuration value as int '''
        value = self.getConfigString(name, default)
        return int(value)

    def getConfigFloat(self, name: str, default: str = None):
        ''' Convenience method for getting a configuration value as float '''
        value = self.getConfigString(name, default)
        return float(value)
