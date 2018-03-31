import os, os.path
from cifsdk.constants import RUNTIME_PATH
import sys

from ._version import get_versions
VERSION = get_versions()['version']
del get_versions

PYVERSION = 2
if sys.version_info > (3,):
    PYVERSION = 3

TOKEN_LENGTH = 40

ROUTER_ADDR = "ipc://{}".format(os.path.join(RUNTIME_PATH, 'router.ipc'))
ROUTER_ADDR = os.getenv('CIF_ROUTER_ADDR', ROUTER_ADDR)

STORE_ADDR = 'ipc://{}'.format(os.path.join(RUNTIME_PATH, 'store.ipc'))
STORE_ADDR = os.getenv('CIF_STORE_ADDR', STORE_ADDR)

HUNTER_ADDR = 'ipc://{}'.format(os.path.join(RUNTIME_PATH, 'hunter.ipc'))
HUNTER_ADDR = os.getenv('CIF_HUNTER_ADDR', HUNTER_ADDR)

HUNTER_SINK_ADDR = 'ipc://{}'.format(os.path.join(RUNTIME_PATH, 'hunter_sink.ipc'))
HUNTER_SINK_ADDR = os.getenv('CIF_HUNTER_SINK_ADDR', HUNTER_SINK_ADDR)

GATHERER_ADDR = 'ipc://{}'.format(os.path.join(RUNTIME_PATH, 'gatherer.ipc'))
GATHERER_ADDR = os.getenv('CIF_GATHERER_ADDR', GATHERER_ADDR)

GATHERER_SINK_ADDR = 'ipc://{}'.format(os.path.join(RUNTIME_PATH, 'gatherer_sink.ipc'))
GATHERER_SINK_ADDR = os.getenv('CIF_GATHERER_SINK_ADDR', GATHERER_SINK_ADDR)

TOKEN_CACHE_DELAY = 5

HUNTER_RESOLVER_TIMEOUT = os.getenv('CIF_HUNTER_RESOLVER_TIMEOUT', 5)

FEEDS_DAYS = 60
FEEDS_LIMIT = 250000
FEEDS_WHITELIST_LIMIT = 75000

HTTPD_FEED_WHITELIST_CONFIDENCE = os.getenv('CIF_HTTPD_FEED_WHITELIST_CONFIDENCE', 3)

ROUTER_STREAM_ADDR = os.getenv('CIF_ROUTER_STREAM_ADDR', 'ipc://stream.ipc')
ROUTER_STREAM_ENABLED = os.getenv('CIF_ROUTER_STREAM_ENABLED', False)

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)
if ENABLED == '1':
    ENABLED = True