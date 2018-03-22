

class PingHandler(object):

    def __init__(self, store):
        self.store = store

    def handle_ping(self, token, data, **kwargs):
        return self.store.ping(token)

    def handle_ping_write(self, token, data, **kwargs):
        return self.store.tokens.write(token)
