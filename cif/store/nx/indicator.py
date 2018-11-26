import os
import time
import networkx as nx
import arrow
import logging
#from networkx.readwrite import json_graph

from csirtg_indicator import Indicator
from cifsdk.constants import VALID_FILTERS, RUNTIME_PATH
from cif.store.plugin.indicator import IndicatorManagerPlugin

GRAPH_PATH = os.path.join(RUNTIME_PATH, 'indicators.gpickle')
GRAPH_PATH = os.getenv('CIF_STORE_NETWORKX_PATH', GRAPH_PATH)

GRAPH_GEXF_PATH = os.path.join(RUNTIME_PATH, 'indicators.gexf')
GRAPH_GEXF_PATH = os.getenv('CIF_STORE_NETWORKX_GEXF_PATH', GRAPH_GEXF_PATH)

REQUIRED_FIELDS = ['provider', 'indicator', 'tags', 'group', 'itype']

TRACE = os.environ.get('CIF_STORE_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


class IndicatorManager(IndicatorManagerPlugin):

    def __init__(self, handle, engine, **kwargs):
        super(IndicatorManager, self).__init__(**kwargs)

        self.handle = nx.Graph()

        if os.path.exists(GRAPH_PATH):
            self.handle = nx.read_gpickle(GRAPH_PATH)

    def is_valid_indicator(self, i):
        if isinstance(i, Indicator):
            i = i.__dict__()

        for f in REQUIRED_FIELDS:
            if not i.get(f):
                raise ValueError("Missing required field: {} for \n{}".format(f, i))

    def create(self, token, data):
        return self.upsert(token, data)

    def search(self, token, filters, limit=500):
        return []

    def delete(self, token, data=None):
        return []

    def upsert(self, token, i):
        g = self.handle

        g.add_node(i['indicator'], itype=i['itype'])
        for t in i.get('tags', []):
            g.add_node(t)
            g.add_edge(i['indicator'], t)

        reported_at = arrow.get(i['reported_at'])
        reported_at = '{}'.format(reported_at.format('YYYY-MM-DD'))
        g.add_node(reported_at)
        g.add_edge(i['indicator'], reported_at)

        for a in ['asn', 'asn_desc', 'cc', 'timezone', 'region', 'city']:
            if not i.get(a):
                continue

            g.add_node(i[a])
            g.add_edge(i['indicator'], i[a])

        if i.get('peers'):
            for p in i['peers']:
                for a in ['asn', 'cc', 'prefix']:
                    g.add_node(p[a])
                    g.add_edge(i['indicator'], p[a])

    def save(self):
        logger.debug("writing graph...")
        s1 = time.time()
        nx.write_gpickle(self.handle, GRAPH_PATH)
        nx.write_gexf(self.handle, GRAPH_GEXF_PATH)
        logger.debug('done: %0.2f' % (time.time() - s1))