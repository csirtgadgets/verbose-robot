import os
import inspect

MOD_PATH = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))

STORE_PATH = os.path.join(MOD_PATH, "store")
RCVTIMEO = 5000
SNDTIMEO = 2000
LINGER = 3
MORE_DATA_NEEDED = -2

STORE_DEFAULT = os.environ.get('CIF_STORE_STORE', 'sqlite')
STORE_PLUGINS = ['cif.store.sqlite', 'cif.store.elasticsearch']

# seconds to flush the queue [interval]
CREATE_QUEUE_FLUSH = os.environ.get('CIF_STORE_QUEUE_FLUSH', 5)

# num of records before we start throttling a token
CREATE_QUEUE_LIMIT = os.environ.get('CIF_STORE_QUEUE_LIMIT', 250)

# seconds of in-activity before we remove from the penalty box
CREATE_QUEUE_TIMEOUT = os.environ.get('CIF_STORE_TIMEOUT', 5)

# queue max to flush before we hit CIF_STORE_QUEUE_FLUSH mark
CREATE_QUEUE_MAX = os.environ.get('CIF_STORE_QUEUE_MAX', 1000)
REQUIRED_ATTRIBUTES = ['group', 'provider', 'indicator', 'itype', 'tags']
TRACE = os.environ.get('CIF_STORE_TRACE')
GROUPS = ['everyone']
