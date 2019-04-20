#!/usr/bin/env python3

import logging
import textwrap
import ujson as json
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import yaml
import arrow
import zmq
import time
import traceback
from base64 import b64decode
from importlib import import_module
from pprint import pprint
from types import GeneratorType

from csirtg_indicator import Indicator
from cifsdk.msg import Msg
from cif.constants import STORE_ADDR, STORE_WRITE_ADDR, STORE_WRITE_H_ADDR
from cifsdk.constants import REMOTE_ADDR, CONFIG_PATH
from cifsdk.exceptions import AuthError, InvalidSearch
from cifsdk.utils import setup_logging, setup_signals, load_plugin
from cif.utils import get_argument_parser
from cif.hunter import CONFIG_PATH as ROUTER_CONFIG_PATH

from cif.utils.process import MyProcess
import cif.store
from cif.utils.manager import Manager as _Manager
from .ping import PingHandler
from .token import TokenHandler
from .helpers import _check_indicator, _cleanup_indicator

from .constants import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


class Manager(_Manager):

    def __init__(self, context):
        _Manager.__init__(self, Store, 1)

        self.socket = context.socket(zmq.DEALER)
        self.socket.bind(STORE_ADDR)

        self.s_write = context.socket(zmq.DEALER)
        self.s_write.bind(STORE_WRITE_ADDR)

        self.s_hunter_write = context.socket(zmq.DEALER)
        self.s_hunter_write.bind(STORE_WRITE_H_ADDR)


class Store(MyProcess):
    def __init__(self, store_type=STORE_DEFAULT, store_address=STORE_ADDR,
                 **kwargs):
        MyProcess.__init__(self)

        self.store_addr = store_address
        self.store = store_type
        self.kwargs = kwargs
        self.create_queue = {}
        self.create_queue_count = 0

        self.router = None
        self.router_write = None
        self.router_write_h = None
        self.context = None

        self._load_plugin(**self.kwargs)

        self.ping_handler = PingHandler(self.store)
        self.token_handler = TokenHandler(self.store)

    def _load_plugin(self, **kwargs):
        p = load_plugin(cif.store.__path__, self.store)

        if p is None:
            p = f"cif_{self.store}"
            p = import_module(p)

            if p is None:
                raise ImportError(f"{self.store} Not Found")

            p = p.Plugin

        self.store = p(**kwargs)

    def _check_create_queue(self, last_flushed):
        if len(self.create_queue) == 0:
            return time.time()

        if ((time.time() - last_flushed) <= CREATE_QUEUE_FLUSH) \
                and (self.create_queue_count < CREATE_QUEUE_MAX):
            return last_flushed

        self._flush_create_queue()

        for t in list(self.create_queue):
            self.create_queue[t]['messages'] = []

            # if we've not seen activity, reset the counter
            if self.create_queue[t]['count'] > 0:
                if (time.time() - self.create_queue[t]['last_activity'])\
                        > CREATE_QUEUE_TIMEOUT:
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
            confidence=4,
            tags='search',
            provider=t['username'],
            first_at=ts,
            last_at=ts,
            reported_at=ts,
            group=t['groups'][0],
            count=1,
        )
        self.store.indicators.create(t, [s.__dict__()])

    def _flush_create_queue(self):
        for t in self.create_queue:
            if len(self.create_queue[t]['messages']) == 0:
                continue

            logger.debug('flushing queue...')
            data = [msg[0] for _, _, msg in self.create_queue[t]['messages']]
            _t = self.store.tokens.write(t)

            try:
                logger.info('inserting %d indicators..', len(data))

                rv = self.store.indicators.upsert(_t, data)
                rv = {"status": "success", "data": rv}

            except AuthError as e:
                rv = {'status': 'failed', 'message': 'unauthorized'}

            for id, client_id, _ in self.create_queue[t]['messages']:
                Msg(id=id, client_id=client_id, mtype=Msg.INDICATORS_CREATE,
                    data=rv)

            if rv['status'] == 'success':
                self.store.tokens.update_last_activity_at(t,
                                                          arrow.utcnow()
                                                          .datetime)

            logger.debug('queue flushed..')

    def start(self):
        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router_write = self.context.socket(zmq.ROUTER)
        self.router_write_h = self.context.socket(zmq.ROUTER)

        t = self.token_handler.token_create_admin()
        if t:
            self.token_handler.token_create_fm(token=t)

        if not os.path.exists(ROUTER_CONFIG_PATH):
            t = self.token_handler.token_create_hunter()
            with open(ROUTER_CONFIG_PATH, 'w') as f:
                f.write('hunter_token: %s' % t)

        self.router.connect(self.store_addr)
        self.router_write.connect(STORE_WRITE_ADDR)
        self.router_write_h.connect(STORE_WRITE_H_ADDR)

        poller = zmq.Poller()
        poller.register(self.router, zmq.POLLIN)

        poller_write = zmq.Poller()
        poller_write.register(self.router_write, zmq.POLLIN)

        poller_write_h = zmq.Poller()
        poller_write_h.register(self.router_write_h, zmq.POLLIN)

        last_flushed = time.time()
        while not self.exit.is_set():
            try:
                s = dict(poller.poll(5))
            except KeyboardInterrupt:
                break

            if self.router in s:
                m = Msg().recv(self.router)
                try:
                    self.handle_message(m)
                except Exception as e:
                    logger.error(e)
                    logger.debug(m)

            try:
                s = dict(poller_write.poll(5))
            except KeyboardInterrupt:
                break

            if self.router_write in s:
                m = Msg().recv(self.router_write)

                try:
                    self.handle_message(m)
                except Exception as e:
                    logger.error(e)
                    logger.debug(m)

            try:
                s = dict(poller_write_h.poll(5))
            except KeyboardInterrupt:
                break

            if self.router_write_h in s:
                m = Msg().recv(self.router_write_h)

                try:
                    self.handle_message(m)
                except Exception as e:
                    logger.error(e)
                    logger.debug(m)

            last_flushed = self._check_create_queue(last_flushed)

        self.router.close()
        self.router_write.close()
        self.router_write_h.close()

    def handle_message(self, m):
        err = None
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

        s = self.router
        if mtype == 'indicators_create':
            s = self.router_write

        Msg(id=id, client_id=client_id, mtype=mtype, data=data).send(s)

        if not err:
            self.store.tokens.update_last_activity_at(token, arrow.utcnow().datetime)

    def _queue_indicator(self, id, token, data, client_id):
        if not self.create_queue.get(token):
            self.create_queue[token] = {'count': 0, "messages": []}

        self.create_queue[token]['count'] += 1
        self.create_queue_count += 1
        self.create_queue[token]['last_activity'] = time.time()
        self.create_queue[token]['messages'].append((id, client_id, [data]))

        return MORE_DATA_NEEDED

    def handle_indicators_create(self, token, data, id=None, client_id=None,
                                 flush=False, force=False):
        # this will raise AuthError if false
        t = self.store.tokens.write(token)

        if len(data) == 1 and not force:
            # queue it..
            data = data[0]

            _check_indicator(data, t)
            _cleanup_indicator(data)

            logger.debug('queuing indicator...')
            return self._queue_indicator(id, token, data, client_id)

        # more than one, send it..
        if isinstance(data, dict):
            data = [data]

        for i in data:
            # this will raise AuthError if the groups don't match
            _check_indicator(i, t)
            _cleanup_indicator(i)

        return self.store.indicators.create(t, data, flush=flush)

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

        if isinstance(x, GeneratorType):
            x = list(x)

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

    def handle_indicators_delete(self, token, data=None, **kwargs):
        t = self.store.tokens.admin(token)
        return self.store.indicators.delete(t, data=data)


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
         Env Variables:
            CIF_RUNTIME_PATH

        example usage:
            $ cif-store -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-store',
        parents=[p]
    )

    p.add_argument("--store", help="store type {} [default: %(default)s]".
                   format(', '.join(STORE_PLUGINS)),
                   default=STORE_DEFAULT)

    p.add_argument('--config', help='specify config path [default %(default)s]'
                   , default=CONFIG_PATH)

    p.add_argument('--token-create-admin', help='generate an admin token',
                   action="store_true")
    p.add_argument('--token-create-fm', action="store_true")
    p.add_argument('--token-create-fm-remote', default=REMOTE_ADDR)
    p.add_argument('--token-create-hunter', action="store_true")
    p.add_argument('--token-create-httpd', action="store_true")

    p.add_argument('--config-path', help='store the token as a config')
    p.add_argument('--token', help='specify the token to use', default=None)
    p.add_argument('--token-groups',
                   help="groups associated with token [default %(default)s]'",
                   default='everyone')

    p.add_argument('--remote', help='specify remote')

    args = p.parse_args()

    groups = args.token_groups.split(',')

    setup_logging(args)

    setup_signals(__name__)

    if not args.token_create_fm and not args.token_create_admin and \
            not args.token_create_hunter and not \
            args.token_create_httpd:
        logger.error('missing required arguments, see -h for more information')
        raise SystemExit

    if args.token_create_fm:
        with Store(store_type=args.store) as s:
            s._load_plugin(store_type=args.store)

            t = s.token_handler.token_create_fm(token=args.token,
                                                groups=groups)
            if t:
                data = {'token': t}
                if args.remote:
                    data['remote'] = args.remote

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info(f'token config generated: {args.token_create_fm}')
            else:
                logger.error('token not created')

    if args.token_create_hunter:
        with Store(store_type=args.store) as s:
            t = s.token_handler.token_create_hunter(token=args.token,
                                                    groups=groups)
            if t:
                data = {'token': t}

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info(f'token config generated: '
                            f'{args.token_create_hunter}')
            else:
                logger.error('token not created')

    if args.token_create_admin:
        with Store(store_type=args.store) as s:
            t = s.token_handler.token_create_admin(token=args.token,
                                                   groups=groups)
            if t:
                data = {'token': t}

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info('token config generated: {}'
                            .format(args.token_create_admin))
            else:
                logger.error('token not created')

    if args.token_create_httpd:
        with Store(store_type=args.store) as s:
            t = s.token_handler.token_create_httpd(token=args.token,
                                                   groups=groups)
            if t:
                data = {'token': t}

                if args.config_path:
                    with open(args.config_path, 'w') as f:
                        f.write(yaml.dump(data, default_flow_style=False))

                logger.info('token config generated: {}'
                            .format(args.token_create_httpd))
            else:
                logger.error('token not created')


if __name__ == "__main__":
    main()
