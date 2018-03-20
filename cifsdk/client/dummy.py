from cifsdk.client import Client
import ujson as json


class Dummy(Client):

    def __init__(self, remote, token):
        self.remote = remote
        self.token = token

    def ping(self, write=False):
        return True

    def indicators_create(self, data):
        if isinstance(data, dict):
            data = self._kv_to_indicator(data)

        if type(data) == dict:
            data = [data]

        return data

    def indicators_search(self, data, decode=True, test_data=[], test_wl=[]):
        if len(test_data) > 0:
            return test_data

        if type(data) == dict:
            data = [data]

        if decode:
            return data

        return json.dumps({'data': data, 'status': 'success', 'message': ''}).encode('utf-8')


Plugin = Dummy
