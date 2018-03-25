#!/usr/bin/env python

import ujson as json
import logging
import textwrap
import traceback
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from time import sleep
import zmq
import os
import sys
from pprint import pprint

from cif.constants import ROUTER_ADDR, STORE_ADDR, HUNTER_ADDR, GATHERER_ADDR, GATHERER_SINK_ADDR, HUNTER_SINK_ADDR, \
    RUNTIME_PATH, ROUTER_STREAM_ADDR, ROUTER_STREAM_ENABLED
from cifsdk.constants import CONFIG_PATH
from cifsdk.utils import setup_logging, get_argument_parser, setup_signals, setup_runtime_path
from cif_hunter import Hunter
from cif.store import Store
from cif_gatherer import Gatherer
from .streamer import Streamer
import time
import multiprocessing as mp
from cifsdk_msg import Msg


HUNTER_MIN_CONFIDENCE = 4
HUNTER_THREADS = os.getenv('CIF_HUNTER_THREADS', 0)
HUNTER_ADVANCED = os.getenv('CIF_HUNTER_ADVANCED', 0)
GATHERER_THREADS = os.getenv('CIF_GATHERER_THREADS', 2)
STORE_DEFAULT = 'sqlite'
STORE_PLUGINS = ['cif.store.dummy', 'cif.store.sqlite', 'cif.store.elasticsearch']

ZMQ_HWM = 1000000
ZMQ_SNDTIMEO = 5000
ZMQ_RCVTIMEO = 5000

FRONTEND_TIMEOUT = os.getenv('CIF_FRONTEND_TIMEOUT', 100)
BACKEND_TIMEOUT = os.getenv('CIF_BACKEND_TIMEOUT', 10)

HUNTER_TOKEN = os.getenv('CIF_HUNTER_TOKEN', None)

STORE_DEFAULT = os.getenv('CIF_STORE_STORE', STORE_DEFAULT)
STORE_NODES = os.getenv('CIF_STORE_NODES')

PIDFILE = os.getenv('CIF_ROUTER_PIDFILE', '%s/cif_router.pid' % RUNTIME_PATH)

TRACE = os.getenv('CIF_ROUTER_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE in [1, '1']:
    logger.setLevel(logging.DEBUG)


class Router(object):

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return self

    def __init__(self, listen=ROUTER_ADDR, store_type=STORE_DEFAULT, store_address=STORE_ADDR, store_nodes=None,
                 hunter_token=HUNTER_TOKEN, hunter_threads=HUNTER_THREADS, gatherer_threads=GATHERER_THREADS,
                 test=False):

        if test:
            return

        self.context = zmq.Context()

        self._init_store(store_address, store_type, nodes=store_nodes)

        self.gatherers = []
        self._init_gatherers(gatherer_threads)

        self.hunters = False
        if hunter_threads:
            self._init_hunters(hunter_threads, hunter_token)

        if ROUTER_STREAM_ENABLED:
            self._init_streamer()

        self._init_frontend(listen)

        self.count = 0
        self.count_start = time.time()

        self.terminate = False

    def _init_streamer(self):
        logger.debug('enabling streamer..')
        self.streamer_s = self.context.socket(zmq.PUSH)
        self.streamer_s.bind(ROUTER_STREAM_ADDR)
        self.streamer = mp.Process(target=Streamer().start)
        self.streamer.start()

    def _init_hunters(self, threads, token):
        if threads == 0:
            return

        logger.info('launching hunters...')
        self.hunter_sink_s = self.context.socket(zmq.ROUTER)
        self.hunter_sink_s.bind(HUNTER_SINK_ADDR)

        self.hunters_s = None
        self.hunters_s = self.context.socket(zmq.PUSH)
        self.hunters_s.bind(HUNTER_ADDR)

        self.hunters = []
        for n in range(int(threads)):
            p = mp.Process(target=Hunter(token=token).start)
            p.start()
            self.hunters.append(p)

    def _init_gatherers(self, threads):
        logger.info('launching gatherers...')
        self.gatherer_s = self.context.socket(zmq.PUSH)
        self.gatherer_sink_s = self.context.socket(zmq.PULL)
        self.gatherer_s.bind(GATHERER_ADDR)
        self.gatherer_sink_s.bind(GATHERER_SINK_ADDR)

        for n in range(int(threads)):
            p = mp.Process(target=Gatherer().start)
            p.start()
            self.gatherers.append(p)

    def _init_store(self, store_address, store_type, nodes=False):
        logger.info('launching store...')
        self.store_s = self.context.socket(zmq.DEALER)
        self.store_s.bind(store_address)
        self.store_p = mp.Process(target=Store(store_address=store_address, store_type=store_type, nodes=nodes).start)
        self.store_p.start()

    def _init_frontend(self, listen):
        logger.info('launching frontend...')
        self.frontend_s = self.context.socket(zmq.ROUTER)
        self.frontend_s.set_hwm(ZMQ_HWM)
        self.frontend_s.bind(listen)

    def stop(self):
        self.terminate = True

        logger.debug('stopping hunters')
        for h in self.hunters:
            h.terminate()

        logger.debug('stopping gatherers')
        for g in self.gatherers:
            g.terminate()

        self.streamer.terminate()
        self.store_p.terminate()

        sleep(0.01)

    def start(self):
        logger.debug('starting loop')

        poller = zmq.Poller()
        poller_backend = zmq.Poller()

        poller_backend.register(self.gatherer_sink_s, zmq.POLLIN)
        poller.register(self.store_s, zmq.POLLIN)

        if self.hunters:
            poller_backend.register(self.hunter_sink_s, zmq.POLLIN)

        poller.register(self.frontend_s, zmq.POLLIN)

        # we use this instead of a loop so we can make sure to get front end queries as they come in
        # that way hunters don't over burden the store, think of it like QoS
        # it's weighted so front end has a higher chance of getting a faster response
        while not self.terminate:
            items = dict(poller.poll(FRONTEND_TIMEOUT))

            if self.frontend_s in items and items[self.frontend_s] == zmq.POLLIN:
                self.handle_message(self.frontend_s)

            if self.store_s in items and items[self.store_s] == zmq.POLLIN:
                self.handle_message_store(self.store_s)

            items = dict(poller_backend.poll(BACKEND_TIMEOUT))

            if self.gatherer_sink_s in items and items[self.gatherer_sink_s] == zmq.POLLIN:
                self.handle_message_gatherer(self.gatherer_sink_s)

            if self.hunters and self.hunter_sink_s in items and items[self.hunter_sink_s] == zmq.POLLIN:
                self.handle_message(self.hunter_sink_s)

    def _log_counter(self):
        self.count += 1
        if (self.count % 100) == 0:
            t = (time.time() - self.count_start)
            n = self.count / t
            logger.info('processing {} msgs per {} sec'.format(round(n, 2), round(t, 2)))
            self.count = 0
            self.count_start = time.time()

    def handle_message(self, s):
        id, token, mtype, data = Msg().recv(s)

        handler = self.handle_message_default
        if mtype in ['indicators_create', 'indicators_search']:
            handler = getattr(self, "handle_" + mtype)

        try:
            handler(id, mtype, token, data)
        except Exception as e:
            logger.error(e)

        self._log_counter()

    def handle_message_default(self, id, mtype, token, data='[]'):
        Msg(id=id, mtype=mtype, token=token, data=data).send(self.store_s)

    def handle_message_store(self, s):
        # re-routing from store to front end
        # id, mtype, token, data = Msg().recv(s)
        # logger.debug('relaying..')
        Msg().recv(s, relay=self.frontend_s)

    def handle_message_gatherer(self, s):
        id, token, mtype, data = Msg().recv(s)

        Msg(id=id, mtype=mtype, token=token, data=data).send(self.store_s)

        if self.hunters is False and not ROUTER_STREAM_ENABLED:
            return

        logger.debug('wati what?"')
        data = json.loads(data)
        if isinstance(data, dict):
            data = [data]

        for d in data:
            s = json.dumps(d)

            if ROUTER_STREAM_ENABLED:
                self.streamer_s.send_string(s)

            if d.get('confidence', 0) >= HUNTER_MIN_CONFIDENCE:
                self.hunters_s.send_string(s)

    def handle_indicators_search(self, id, mtype, token, data):
        self.handle_message_default(id, mtype, token, data)

        if self.hunters:
            self.hunters_s.send_string(data)

        if ROUTER_STREAM_ENABLED:
            self.streamer_s.send_string(data)

    def handle_indicators_create(self, id, mtype, token, data):
        Msg(id=id, mtype=mtype, token=token, data=data).send(self.gatherer_s)


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CIF_RUNTIME_PATH
            CIF_ROUTER_CONFIG_PATH
            CIF_ROUTER_ADDR
            CIF_HUNTER_ADDR
            CIF_HUNTER_TOKEN
            CIF_HUNTER_THREADS
            CIF_GATHERER_THREADS
            CIF_STORE_ADDR

        example usage:
            $ cif-router --listen 0.0.0.0 -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-router',
        parents=[p]
    )

    p.add_argument('--config', help='specify config path [default: %(default)s', default=CONFIG_PATH)
    p.add_argument('--listen', help='address to listen on [default: %(default)s]', default=ROUTER_ADDR)

    p.add_argument('--gatherer-threads', help='specify number of gatherer threads to use [default: %(default)s]',
                   default=GATHERER_THREADS)

    p.add_argument('--hunter', help='address hunters listen on on [default: %(default)s]', default=HUNTER_ADDR)
    p.add_argument('--hunter-token', help='specify token for hunters to use [default: %(default)s]',
                   default=HUNTER_TOKEN)
    p.add_argument('--hunter-threads', help='specify number of hunter threads to use [default: %(default)s]',
                   default=HUNTER_THREADS)

    p.add_argument("--store-address", help="specify the store address cif-router is listening on[default: %("
                                           "default)s]", default=STORE_ADDR)

    p.add_argument("--store", help="specify a store type {} [default: %(default)s]".format(', '.join(STORE_PLUGINS)),
                   default=STORE_DEFAULT)

    p.add_argument('--store-nodes', help='specify storage nodes address [default: %(default)s]', default=STORE_NODES)

    p.add_argument('--logging-ignore', help='set logging to WARNING for specific modules')

    p.add_argument('--pidfile', help='specify pidfile location [default: %(default)s]', default=PIDFILE)

    args = p.parse_args()
    setup_logging(args)

    if args.verbose:
        logger.setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    if args.logging_ignore:
        to_ignore = args.logging_ignore.split(',')

        for i in to_ignore:
            logging.getLogger(i).setLevel(logging.WARNING)

    setup_runtime_path(args.runtime_path)
    setup_signals(__name__)

    # http://stackoverflow.com/a/789383/7205341
    pid = str(os.getpid())
    logger.debug("pid: %s" % pid)

    if os.path.isfile(args.pidfile):
        logger.critical("%s already exists, exiting" % args.pidfile)
        raise SystemExit

    with Router(listen=args.listen, store_type=args.store, store_address=args.store_address,
                store_nodes=args.store_nodes, hunter_token=args.hunter_token, hunter_threads=args.hunter_threads,
                gatherer_threads=args.gatherer_threads) as r:

        try:
            pidfile = open(args.pidfile, 'w')
            pidfile.write(pid)
            pidfile.close()
        except PermissionError as e:
            logger.error('unable to create pid %s' % args.pidfile)

        try:
            logger.info('starting router..')
            r.start()

        except KeyboardInterrupt:
            # todo - signal to threads to shut down and wait for them to finish
            logger.info('shutting down via SIGINT...')

        except SystemExit:
            logger.info('shutting down via SystemExit...')

        except Exception as e:
            logger.critical(e)
            traceback.print_exc()

        r.stop()
        if os.path.isfile(args.pidfile):
            os.unlink(args.pidfile)

    logger.info('Shutting down')
    if os.path.isfile(args.pidfile):
        os.unlink(args.pidfile)


if __name__ == "__main__":
    main()
