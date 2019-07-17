#!/usr/bin/env python3

import logging
import os
import traceback
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import zmq
from json import loads, dumps
import re
from pprint import pprint

# https://github.com/gevent/gevent/issues/1016
from gevent import monkey
monkey.patch_all()

from flask import Flask, request, _request_ctx_stack, session, make_response
from flask_cors import CORS
from flask_compress import Compress
from flask_restplus import Api
from werkzeug.contrib.fixers import ProxyFix
from flask_sockets import Sockets

from cifsdk.utils import setup_logging, setup_runtime_path
from cif.utils import get_argument_parser
from cifsdk.client.zmq import ZMQ as Client
from cifsdk.constants import ROUTER_ADDR
from cifsdk.exceptions import AuthError, TimeoutError, InvalidSearch
from .constants import HTTP_LISTEN, HTTP_LISTEN_PORT, TRACE, PIDFILE, \
    SECRET_KEY

from .indicators import api as indicators_api
from .ping import api as ping_api
from .tokens import api as tokens_api
from .health import api as health_api
from .stats import api as stats_api
from .predict import api as predict_api

STREAM_ADDR = os.getenv('CIF_STREAM_ADDR', 'tcp://127.0.0.1:5001')

# from .stats import api as stats_api

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

CORS(app, resources={r"/*": {"origins": "*"}})
Compress(app)

sockets = Sockets(app)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

# http://flask-restplus.readthedocs.io/en/stable/swagger.html#documenting-authorizations
api = Api(app, version='4.0', title='CIFv4 API',
          description='The CIFv4 REST API', authorizations=authorizations,
          security='apikey')


def output_csv(data, code, headers=None):
    resp = make_response(data, code)
    resp.headers.extend(headers or {})
    return resp


api.representations['text/plain'] = output_csv

#firehose_api = Namespace('firehose', description='Firehose (WebSockets)')

APIS = [
    ping_api,
    indicators_api,
    tokens_api,
    health_api,
    stats_api,
    predict_api,
    #firehose_api,
]

for A in APIS:
    api.add_namespace(A)

app.secret_key = SECRET_KEY

log_level = logging.WARN
if TRACE == '1':
    log_level = logging.DEBUG
    logging.getLogger('flask_cors').level = logging.INFO

console = logging.StreamHandler()
logging.getLogger('gunicorn.error').setLevel(log_level)
logging.getLogger('gunicorn.error').addHandler(console)
logger = logging.getLogger('gunicorn.error')


def pull_token():
    if "Authorization" not in request.headers:
        return

    t = request.headers['Authorization']
    if not t:
        return

    return t


def _search_bulk(filters):
    try:
        with Client(ROUTER_ADDR, session['token']) as client:
            r = client.indicators_search(filters)

    except InvalidSearch as e:
        return api.abort(400)

    except AuthError as e:
        return api.abort(401)

    except zmq.error.Again as e:
        return api.abort(503)

    except Exception as e:
        logger.error(e)
        if logger.getEffectiveLevel() == logging.DEBUG:
            traceback.print_exc()

        if 'invalid search' in str(e):
            return api.abort(400, str(e))

        return api.abort(500)

    return r


@app.route('/indicators/bulk', methods=['POST'])
@app.route('/indicators/bulk/', methods=['POST'])
def search_bulk():
    if request.data == b'':
        return 'invalid search', 400

    data = request.data.decode('utf-8')

    try:
        data = loads(data)
    except:
        return 'invalid search', 400

    results = _search_bulk(data)

    return dumps(results), 200

# https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent
# need to thread this out in dev mode
@sockets.route('/firehose')
@api.response(401, 'Unauthorized')
@api.response(200, 'OK')
@api.doc('firehose')
def firehose(ws):
    """Firehose"""

    t = pull_token()

    # check authorization
    try:
        r = Client(ROUTER_ADDR, t).tokens_search(filters={'q': t})
        if not r:
            return api.abort(401)
    except TimeoutError:
        return api.abort(408)

    except AuthError:
        return api.abort(401)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return api.abort(503)

    ctx = zmq.Context()
    router = ctx.socket(zmq.SUB)

    logger.debug('connecting: %s' % STREAM_ADDR)
    router.connect(STREAM_ADDR)

    router.setsockopt(zmq.SUBSCRIBE, b'')

    poller = zmq.Poller()
    poller.register(router, zmq.POLLIN)

    ws.send("connected")
    while not ws.closed:
        try:
            s = dict(poller.poll(5000))
        except KeyboardInterrupt or SystemExit:
            break

        if ws.closed:
            break

        if len(s) == 0:
            try:
                ws.send('ping')
            except Exception as e:
                break

            m = ws.receive()
            if m != 'pong':
                break

        if router not in s:
            continue

        message = router.recv_multipart()
        ws.send(message[0])

    logger.debug('cleaning up ws client..')
    router.close()
    del router


@app.before_request
def before_request():
    """
    Grab the API token from headers

    :return: 401 if no token is present
    """

    if request.method == 'GET' and \
            request.endpoint in ['/', 'doc', 'help', 'health', 'restplus_doc.static', 'specs', 'swaggerui']:
        return

    if request.method == 'GET' and request.endpoint in ['favicon']:
        return api.abort(404)

    method = request.form.get('_method', '').upper()
    if method:
        request.environ['REQUEST_METHOD'] = method
        ctx = _request_ctx_stack.top
        ctx.url_adapter.default_method = method
        assert request.method == method

    t = pull_token()
    if not t and HTTP_LISTEN == '127.0.0.1' and not app.config.get('dummy'):
        session['token'] = 'TEST-TOKEN'
        return

    if not t or t == 'None':
        return api.abort(401)

    session['token'] = t


def main():
    from gevent import pywsgi, pool
    from geventwebsocket.handler import WebSocketHandler

    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        example usage:
            $ cif-httpd -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-httpd',
        parents=[p]
    )

    p.add_argument('--fdebug', action='store_true')

    args = p.parse_args()
    setup_logging(args)

    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    setup_runtime_path(args.runtime_path)

    if not args.fdebug:
        # http://stackoverflow.com/a/789383/7205341
        pid = str(os.getpid())
        logger.debug("pid: %s" % pid)

        if os.path.isfile(PIDFILE):
            logger.critical("%s already exists, exiting" % PIDFILE)
            raise SystemExit

        try:
            pidfile = open(PIDFILE, 'w')
            pidfile.write(pid)
            pidfile.close()
        except PermissionError as e:
            logger.error('unable to create pid %s' % PIDFILE)

    try:
        logger.info('pinging router...')
        logger.info('starting up...')

        #app.run(host=HTTP_LISTEN, port=HTTP_LISTEN_PORT, debug=args.fdebug, threaded=True)
        mypool = pool.Pool(500)
        server = pywsgi.WSGIServer((HTTP_LISTEN, HTTP_LISTEN_PORT), app, spawn=mypool, handler_class=WebSocketHandler)
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info('shutting down...')

    except Exception as e:
        logger.critical(e)
        traceback.print_exc()

    if os.path.isfile(PIDFILE):
        os.unlink(PIDFILE)


if __name__ == "__main__":
    main()
