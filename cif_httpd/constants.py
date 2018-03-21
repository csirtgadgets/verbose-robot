import os, os.path
import tempfile
import sys

PYVERSION = 2
if sys.version_info > (3,):
    PYVERSION = 3

from . import __version__ as VERSION

RUNTIME_PATH = os.getcwd()
ROUTER_ADDR = 'ipc://router.ipc'

HTTP_LISTEN = os.getenv('CIF_HTTPD_LISTEN', '127.0.0.1')

TRACE = os.getenv('CIF_HTTPD_TRACE', 0)
HTTP_LISTEN_PORT = os.getenv('CIF_HTTPD_LISTEN_PORT', 5000)

PIDFILE = os.getenv('CIF_HTTPD_PIDFILE', '{}/cif_httpd.pid'.format(RUNTIME_PATH))

# NEEDS TO BE STATIC TO WORK WITH SESSIONS
SECRET_KEY = os.getenv('CIF_HTTPD_SECRET_KEY', os.urandom(24))
HTTPD_TOKEN = os.getenv('CIF_HTTPD_TOKEN')

HTTPD_PROXY = os.getenv('CIF_HTTPD_PROXY')

TOKEN_FILTERS = ['username', 'token']

TEMP_DIR = os.path.join(tempfile.gettempdir())
RUNTIME_PATH = os.getenv('CIF_RUNTIME_PATH', TEMP_DIR)
RUNTIME_PATH = os.path.join(RUNTIME_PATH)

# Logging stuff
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s][%(threadName)s] - %(message)s'

LOGLEVEL = 'ERROR'
LOGLEVEL = os.getenv('CIF_LOGLEVEL', LOGLEVEL).upper()