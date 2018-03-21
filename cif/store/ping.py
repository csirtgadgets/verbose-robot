

class PingHandler(object):

    def __init__(self, store):
        self.store = store

    def handle_ping(self, token, **kwargs):
        return self.store.ping(token)

    def handle_ping_write(self, token, **kwargs):
        return self.store.tokens.write(token)