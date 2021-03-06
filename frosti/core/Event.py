
class Event:
    def __init__(self, name: str=None, data: dict={}):
        self._data = data.copy()
        self.__name = name
        if name is None:
            name = type(self).__name__

    def __repr__(self):
        return self.__name

    @property
    def data(self):
        return self._data.copy()
