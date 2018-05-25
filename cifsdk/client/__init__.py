import abc
from csirtg_indicator import Indicator


class Client(object):

    def __init__(self, remote, token, **kwargs):
        self.remote = remote
        self.token = str(token)

        self.fireball = kwargs.get('fireball', False)

    def _kv_to_indicator(self, kv):
        return Indicator(**kv)

    @abc.abstractmethod
    def ping(self):
        raise NotImplementedError

    @abc.abstractmethod
    def ping_write(self):
        raise NotImplementedError

    def search(self, data):
        return self.indicators_search(data)

    @abc.abstractmethod
    def indicators_create(self, data):
        raise NotImplementedError

    @abc.abstractmethod
    def indicators_search(self, data):
        raise NotImplementedError

    @abc.abstractmethod
    def stats_search(self, data):
        raise NotImplementedError
