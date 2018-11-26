import logging
import os

from cif.store.plugin import Store
from cif.store.nx.indicator import IndicatorManager
from cif.store.nx.token import TokenManager

logger = logging.getLogger(__name__)
TRACE = os.environ.get('CIF_STORE_NETWORKX_TRACE', '0')
FLUSH = os.environ.get('CIF_STORE_NETWORKX_FLUSH', 60)


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Networkx(Store):
    # http://www.pythoncentral.io/sqlalchemy-orm-examples/
    name = 'networkx'

    def __init__(self, **kwargs):

        self.tokens = TokenManager(None, None)
        self.indicators = IndicatorManager(None, None)

    def ping(self, t):
        if self.tokens.read(t):
            return True

    def ping_write(self, t):
        if self.tokens.write(t):
            return True

    def save(self):
        self.tokens.save()
        self.indicators.save()


Plugin = Networkx
