#!/usr/bin/env python3

import inspect
import logging
import os
import textwrap
import ujson as json
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import yaml
from pprint import pprint
import arrow
import zmq
import time
import traceback
from base64 import b64decode

from csirtg_indicator import Indicator
from cifsdk.msg import Msg
from cif.constants import STORE_ADDR, PYVERSION
from cifsdk.constants import REMOTE_ADDR, CONFIG_PATH, TOKEN
from cifsdk.exceptions import AuthError, InvalidSearch
from cifsdk.utils import setup_logging, get_argument_parser, setup_signals, load_plugin

from cif.utils.process import MyProcess
import cif.store
from .ping import PingHandler
from .token import TokenHandler

MOD_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
STORE_PATH = os.path.join(MOD_PATH, "store")
RCVTIMEO = 5000
SNDTIMEO = 2000
LINGER = 3
MORE_DATA_NEEDED = -2

STORE_DEFAULT = os.environ.get('CIF_STORE_STORE', 'sqlite')
STORE_PLUGINS = ['cif.store.dummy', 'cif.store.sqlite', 'cif.store.elasticsearch']
CREATE_QUEUE_FLUSH = os.environ.get('CIF_STORE_QUEUE_FLUSH', 5)  # seconds to flush the queue [interval]
CREATE_QUEUE_LIMIT = os.environ.get('CIF_STORE_QUEUE_LIMIT', 250)  # num of records before we start throttling a token

# seconds of in-activity before we remove from the penalty box
CREATE_QUEUE_TIMEOUT = os.environ.get('CIF_STORE_TIMEOUT', 5)

# queue max to flush before we hit CIF_STORE_QUEUE_FLUSH mark
CREATE_QUEUE_MAX = os.environ.get('CIF_STORE_QUEUE_MAX', 1000)
REQUIRED_ATTRIBUTES = ['group', 'provider', 'indicator', 'itype', 'tags']
TRACE = os.environ.get('CIF_STORE_TRACE')
GROUPS = ['everyone']

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


class Store(MyProcess):
    def __init__(self, store_type=STORE_DEFAULT, store_address=STORE_ADDR, **kwargs):
        MyProcess.__init__(self)

        self.store_addr = store_address
        self.store = store_type
        self.kwargs = kwargs
        self.create_queue = {}
        self.create_queue_flush = CREATE_QUEUE_FLUSH
        self.create_queue_limit = CREATE_QUEUE_LIMIT
        self.create_queue_wait = CREATE_QUEUE_TIMEOUT
        self.create_queue_max = CREATE_QUEUE_MAX
        self.create_queue_count = 0

        self.router = None
        self.context = None

        self._load_plugin(**self.kwargs)

        self.ping_handler = PingHandler(self.store)
        self.token_handler = TokenHandler(self.store)

    def _load_plugin(self, **kwargs):
        logger.debug('store is: {}'.format(self.store))
        p = load_plugin(cif.store.__path__, self.store)
        self.store = p(**kwargs)

    def _check_create_queue(self, last_flushed):
        if len(self.create_queue) == 0:
            return time.time()

        if ((time.time() - last_flushed) <= self.create_queue_flush) \
                and (self.create_queue_count < self.create_queue_max):
            return last_flushed

        self._flush_create_queue()

        for t in list(self.create_queue):
            self.create_queue[t]['messages'] = []

            # if we've not seen activity, reset the counter
            if self.create_queue[t]['count'] > 0:
                if (time.time() - self.create_queue[t]['last_activity']) > self.create_queue_wait:
                    logger.debug('pruning {} from create_queue'.format(t))
                    del self.create_queue[t]

        self.create_queue_count = 0

        return time.time()

    def _log_search(self, t, data):
        if not data.get('indicator'):
            return

        if data.get('nolog') in ['1', 'True', 1, True]:
            return

        if '*' in data.get('indicator'):
            return

        if '%' in data.get('indicator'):
            return

        ts = arrow.utcnow().format('YYYY-MM-DDTHH:mm:ss.SSZ')
        s = Indicator(
            indicator=data['indicator'],
            tlp='amber',
            confidence=10,
            tags='search',
            provider=t['username'],
            first_at=ts,
            last_at=ts,
            reported_at=ts,
            group=t['groups'][0],
            count=1,
        )
        self.store.indicators.upsert(t, [s.__dict__()])

    def _flush_create_queue(self):
        for t in self.create_queue:
            if len(self.create_queue[t]['messages']) == 0:
                return

            logger.debug('flushing queue...')
            data = [msg[0] for _, _, msg in self.create_queue[t]['messages']]
            _t = self.store.tokens.write(t)
            try:
                start_time = time.time()
                logger.info('inserting %d indicators..', len(data))

                rv = self.store.indicators.upsert(_t, data)

                n = len(data)
                t_time = time.time() - start_time
                logger.info('inserting %d indicators.. took %0.2f seconds (%0.2f/sec)', n, t_time, (n / t_time))
                rv = {"status": "success", "data": rv}

            except AuthError as e:
                rv = {'status': 'failed', 'message': 'unauthorized'}

            for id, client_id, _ in self.create_queue[t]['messages']:
                Msg(id=id, client_id=client_id, mtype=Msg.INDICATORS_CREATE, data=rv)

            if rv['status'] == 'success':
                self.store.tokens.update_last_activity_at(t, arrow.utcnow().datetime)

            logger.debug('queue flushed..')

    def start(self):
        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)

        t = self.token_handler.token_create_admin()
        if t:
            self.token_handler.token_create_smrt(token=t)

        from cif.hunter import CONFIG_PATH as ROUTER_CONFIG_PATH
        if not os.path.exists(ROUTER_CONFIG_PATH):
            t = self.token_handler.token_create_hunter()
            with open(ROUTER_CONFIG_PATH, 'w') as f:
                f.write('hunter_token: %s' % t)

        self.router.connect(self.store_addr)

        poller = zmq.Poller()
        poller.register(self.router, zmq.POLLIN)

        last_flushed = time.time()
        while not self.exit.is_set():
            try:
                s = dict(poller.poll(1000))
            except KeyboardInterrupt:
                break

            if self.router in s:
                m = Msg().recv(self.router)
                try:
                    self.handle_message(m)
                except Exception as e:
                    logger.error(e)
                    logger.debug(m)

            last_flushed = self._check_create_queue(last_flushed)

    def handle_message(self, m):
        err = None
        logger.debug(m)
        id, client_id, token, mtype, data = m

        try:
            data = json.loads(data)
        except ValueError as e:
            logger.error(e)
            data = json.dumps({"status": "failed"})
            Msg(id=id, client_id=client_id, mtype=mtype, data=data).send(self.router)
            return

        if mtype.startswith('tokens'):
            handler = getattr(self.token_handler, "handle_" + mtype)

        elif mtype.startswith('ping'):
            handler = getattr(self.ping_handler, 'handle_%s' % mtype)

        else:
            handler = getattr(self, 'handle_%s' % mtype)

        if not handler:
            logger.error('message type {0} unknown'.format(mtype))
            Msg(id=id, client_id=client_id, mtype=mtype, data='0').send(self.router)
            return

        rv = False
        try:
            rv = handler(token, data, id=id, client_id=client_id)

        except AuthError as e:
            logger.error(e)
            err = 'unauthorized'

        except InvalidSearch as e:
            err = 'invalid search'

        except ValueError as e:
            err = 'invalid indicator {}'.format(e)

        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            err = 'unknown failure'

        if rv == MORE_DATA_NEEDED:
            rv = {"status": "success", "data": '1'}
        else:
            rv = {"status": "success", "data": rv}

        if err:
            rv = {'status': 'failed', 'message': err}

        try:
            data = json.dumps(rv)
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            data = json.dumps({'status': 'failed', 'message': 'feed too large, retry the query'})

        Msg(id=id, client_id=client_id, mtype=mtype, data=data).send(self.router)

        if not err:
            self.store.tokens.update_last_activity_at(token, arrow.utcnow().datetime)

    def _check_indicator(self, i, t):
        if not i.get('group'):
            i['group'] = t['groups'][0]

        if not i.get('provider'):
            i['provider'] = t['username']

        if not i.get('tags'):
            i['tags'] = 'suspicious'

        for e in REQUIRED_ATTRIBUTES:
            if not i.get(e):
                raise ValueError('missing %s' % e)

        if i['group'] not in t['groups']:
            raise AuthError('unable to write to %s' % i['group'])

        return True

    def _cleanup_indicator(self, i):
        if not i.get('message'):
            return

        try:
            i['message'] = b64decode(i['message'])
        except Exception as e:
            pass

    def _queue_indicator(self, id, token, data, client_id):
        if not self.create_queue.get(token):
            self.create_queue[token] = {'count': 0, "messages": []}

        self.create_queue[token]['count'] += 1
        self.create_queue_count += 1
        self.create_queue[token]['last_activity'] = time.time()
        self.create_queue[token]['messages'].append((id, client_id, [data]))

        return MORE_DATA_NEEDED

    def handle_indicators_create(self, token, data, id=None, client_id=None, flush=False):
        # this will raise AuthError if false
        t = self.store.tokens.write(token)

        if len(data) == 1:
            # queue it..
            data = data[0]

            self._check_indicator(data, t)
            self._cleanup_indicator(data)

            logger.debug('queuing indicator...')
            return self._queue_indicator(id, token, data, client_id)

        # more than one, send it..
        if isinstance(data, dict):
            data = [data]

        for i in data:
            # this will raise AuthError if the groups don't match
            self._check_indicator(i, t)
            self._cleanup_indicator(i)

        return self.store.indicators.upsert(t, data, flush=flush)

    def handle_indicators_search(self, token, data, **kwargs):
        t = self.store.tokens.read(token)
        self._log_search(t, data)

        try:
            x = self.store.indicators.search(t, data)
        except Exception as e:
            logger.error(e)

            if logger.getEffectiveLevel() == logging.DEBUG:
                import traceback
                traceback.print_exc()

            raise InvalidSearch('invalid search')

        return x

    def handle_graph_search(self, token, data, **kwargs):
        t = self.store.tokens.read(token)
        try:
            x = self.store.indicators.search_graph(t, data)
        except Exception as e:
            logger.error(e)

            if logger.getEffectiveLevel() == logging.DEBUG:
                traceback.print_exc()

            raise InvalidSearch('invalid search')

        return x

    def handle_stats_search(self, token, data, **kwargs):
        t = self.store.tokens.read(token)

        try:
            x = self.store.indicators.stats_search(t, data)
        except Exception as e:
            logger.error(e)

            if logger.getEffectiveLevel() == logging.DEBUG:
                traceback.print_exc()

            raise InvalidSearch('invalid search')

        return x

    def handle_indicators_delete(self, token, data=None, id=None, client_id=None):
        t = self.store.tokens.admin(token)
        return self.store.indicators.delete(t, data=data)


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
         Env Variables:
            CIF_RUNTIME_PATH
            CIF_STORE_ADDR

        example usage:
            $ cif-store -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-store',
        parents=[p]
    )

    p.add_argument("--store-address", help="specify the store address cif-router is listening on[default: %("
                                           "default)s]", default=STORE_ADDR)

    p.add_argument("--store", help="specify a store type {} [default: %(default)s]".format(', '.join(STORE_PLUGINS)),
                   default=STORE_DEFAULT)

    p.add_argument('--nodes')

    p.add_argument('--config', help='specify config path [default %(default)s]', default=CONFIG_PATH)

    p.add_argument('--token-create-admin', help='generate an admin token', action="store_true")
    p.add_argument('--token-create-smrt', action="store_true")
    p.add_argument('--token-create-smrt-remote', default=REMOTE_ADDR)
    p.add_argument('--token-create-hunter', action="store_true")
    p.add_argument('--token-create-httpd', action="store_true")

    p.add_argument('--config-path', help='store the token as a config')
    p.add_argument('--token', help='specify the token to use', default=None)
    p.add_argument('--token-groups', help="specify groups associated with token [default %(default)s]'",
                   default='everyone')

    p.add_argument('--remote', help='specify remote')

    args = p.parse_args()

    groups = args.token_groups.split(',')

    setup_logging(args)
    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    setup_signals(__name__)

    if not args.token_create_smrt and not args.token_create_admin and not args.token_create_hunter and not \
            args.token_create_httpd:
        logger.error('missing required arguments, see -h for more information')
        raise SystemExit

    if args.token_create_smrt:
        with Store(store_type=args.store, nodes=args.nodes) as s:
            s._load_plugin(store_type=args.store, nodes=args.nodes)

            t = s.token_handler.token_create_smrt(token=args.token, groups=groups)
            if t:
                if PYVERSION == 2:
                    t = t.encode('utf-8')

                data = {
                    'token': t,
                }
                if args.remote:
                    data['remote'] = args.remote

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info('token config generated: {}'.format(args.token_create_smrt))
            else:
                logger.error('token not created')

    if args.token_create_hunter:
        with Store(store_type=args.store, nodes=args.nodes) as s:
            #s._load_plugin(store_type=args.store, nodes=args.nodes)
            t = s.token_handler.token_create_hunter(token=args.token, groups=groups)
            if t:
                if PYVERSION == 2:
                    t = t.encode('utf-8')

                data = {
                    'hunter_token': t,
                }

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info('token config generated: {}'.format(args.token_create_hunter))
            else:
                logger.error('token not created')

    if args.token_create_admin:
        with Store(store_type=args.store, nodes=args.nodes) as s:
            s._load_plugin(store_type=args.store, nodes=args.nodes)
            t = s.token_handler.token_create_admin(token=args.token, groups=groups)
            if t:
                if PYVERSION == 2:
                    t = t.encode('utf-8')

                data = {
                    'token': t,
                }

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info('token config generated: {}'.format(args.token_create_admin))
            else:
                logger.error('token not created')

    if args.token_create_httpd:
        with Store(store_type=args.store, nodes=args.nodes) as s:
            s._load_plugin(store_type=args.store, nodes=args.nodes)
            t = s.token_handler.token_create_httpd(token=args.token, groups=groups)
            if t:
                if PYVERSION == 2:
                    t = t.encode('utf-8')

                data = {
                    'token': t,
                }

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info('token config generated: {}'.format(args.token_create_httpd))
            else:
                logger.error('token not created')


if __name__ == "__main__":
    main()
