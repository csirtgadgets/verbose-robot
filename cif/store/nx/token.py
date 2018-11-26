import os
import time
import networkx as nx
import arrow
import logging
from networkx.readwrite import json_graph

from csirtg_indicator import Indicator
from cifsdk.constants import VALID_FILTERS, RUNTIME_PATH
from cif.store.plugin.token import TokenManagerPlugin

GRAPH_PATH = os.path.join(RUNTIME_PATH, 'tokens.gpickle')
GRAPH_PATH = os.getenv('CIF_STORE_NETWORKX_PATH', GRAPH_PATH)

TRACE = os.environ.get('CIF_STORE_NX_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


class TokenManager(TokenManagerPlugin):

    def __init__(self, handle, engine, **kwargs):
        super(TokenManager, self).__init__(**kwargs)

        self.handle = nx.Graph()

        if os.path.exists(GRAPH_PATH):
            self.handle = nx.read_gpickle(GRAPH_PATH)

    def create(self, data):
        if data.get('token') is None:
            data['token'] = self._generate()

        if isinstance(data.get('acl'), list):
            data['acl'] = ','.join(data['acl'])

        g = self.handle

        for e in ['username', 'acl', 'read', 'write', 'expires_at', 'admin']:
            if not data.get(e):
                continue

            g.add_edge(data['token'], data[e], label=e)

        groups = data.get('groups', 'everyone')
        if isinstance(groups, str):
            groups = [groups]

        for gg in groups:
            g.add_edge(data['token'], gg, label='group')

        self.save()
        return data

    def search(self, data):
        g = self.handle

        # https://stackoverflow.com/questions/15644684/best-practices-for-querying-graphs-by-edge-and-node-attributes-in-networkx
        return []

    def delete(self, token, data=None):
        return []

    def save(self):
        logger.debug("writing graph...")
        s1 = time.time()
        nx.write_gpickle(self.handle, GRAPH_PATH)
        logger.debug('done: %0.2f' % (time.time() - s1))
