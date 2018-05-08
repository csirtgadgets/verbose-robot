from ._version import get_versions
VERSION = get_versions()['version']
del get_versions

import os.path
import tempfile
import sys
from csirtg_indicator.constants import COLUMNS

PYVERSION = 2
if sys.version_info > (3,):
    PYVERSION = 3

TEMP_DIR = os.path.join(tempfile.gettempdir())
RUNTIME_PATH = os.getenv('CIF_RUNTIME_PATH', TEMP_DIR)
DATA_PATH = os.getenv('CIF_DATA_PATH', TEMP_DIR)


# Logging stuff
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s][%(threadName)s] - %(message)s'

LOGLEVEL = 'ERROR'
LOGLEVEL = os.getenv('CIF_LOGLEVEL', LOGLEVEL).upper()

CONFIG_PATH = os.getenv('CIF_CONFIG_PATH', os.path.join(os.getcwd(), 'cif.yml'))
if not os.path.isfile(CONFIG_PATH):
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.cif.yml')

# address stuff

REMOTE_ADDR = 'http://localhost:5000'
REMOTE_ADDR = os.getenv('CIF_REMOTE_ADDR', REMOTE_ADDR)

ROUTER_ADDR = "ipc://{}".format(os.path.join(RUNTIME_PATH, 'router.ipc'))
ROUTER_ADDR = os.getenv('CIF_ROUTER_ADDR', ROUTER_ADDR)

SEARCH_LIMIT = os.getenv('CIF_SEARCH_LIMIT', 500)

TOKEN = os.getenv('CIF_TOKEN', None)
FORMAT = os.getenv('CIF_FORMAT', 'table')

ADVANCED = os.getenv('CIF_ADVANCED')

COLUMNS = os.getenv('CIFSDK_COLUMNS', COLUMNS)
if not isinstance(COLUMNS, list):
    COLUMNS = COLUMNS.split(',')


MAX_FIELD_SIZE = 30

VALID_FILTERS = ['indicator', 'itype', 'confidence', 'provider', 'limit', 'application', 'nolog', 'tags', 'days',
                 'hours', 'groups', 'reported_at', 'cc', 'asn', 'asn_desc', 'rdata', 'first_at', 'last_at', 'region',
                 'probability', 'no_feed', 'days', 'hours', 'today', 'latitude', 'longitude', 'probability']
