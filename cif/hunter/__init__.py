#!/usr/bin/env python3

import ujson as json
import logging
import zmq
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import os

from cifsdk.client.zmq import ZMQ as Client
from cif.constants import HUNTER_ADDR, HUNTER_SINK_ADDR
from csirtg_indicator import Indicator
from cifsdk.utils import setup_runtime_path, setup_logging, get_argument_parser, load_plugins, settings

from cif.utils.process import MyProcess
import cif.hunter
from cif.manager import Manager as _Manager

logger = logging.getLogger(__name__)

SNDTIMEO = 15000
ZMQ_HWM = 1000000
EXCLUDE = os.environ.get('CIF_HUNTER_EXCLUDE', None)
HUNTER_ADVANCED = os.getenv('CIF_HUNTER_ADVANCED', 0)

CONFIG_PATH = os.environ.get('CIF_ROUTER_CONFIG_PATH', 'router.yml')
if not os.path.isfile(CONFIG_PATH):
    CONFIG_PATH = os.environ.get('CIF_ROUTER_CONFIG_PATH', os.path.join(os.path.expanduser('~'), 'router.yml'))

TRACE = os.environ.get('CIF_HUNTER_TRACE', False)

TOKEN = os.getenv('CIF_HUNTER_TOKEN')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE in [1, '1']:
    logger.setLevel(logging.DEBUG)


class Manager(_Manager):

    def __init__(self, context, threads=2):
        _Manager.__init__(self, Hunter, threads)

        self.sink = context.socket(zmq.ROUTER)
        self.sink.bind(HUNTER_SINK_ADDR)

        self.socket = context.socket(zmq.PUSH)
        self.socket.bind(HUNTER_ADDR)


class Hunter(MyProcess):
    def __init__(self, token=TOKEN):
        MyProcess.__init__(self)

        self.token = token
        self.exclude = {}
        self.settings = settings(CONFIG_PATH)

        self._init_token()
        self._init_exclude()

    def _init_token(self):
        if self.token:
            return

        if self.settings and self.settings.get('hunter_token'):
            self.token = self.settings['hunter_token']
            logger.info('token: %s' % self.token)
        else:
            logger.error('missing hunter token')
            self.terminate()

    def _init_exclude(self):
        if not EXCLUDE:
            return

        for e in EXCLUDE.split(','):
            provider, tag = e.split(':')

            if not self.exclude.get(provider):
                self.exclude[provider] = set()

            logger.debug('setting hunter to skip: {}/{}'.format(provider, tag))
            self.exclude[provider].add(tag)

    def start(self):
        plugins = load_plugins(cif.hunter.__path__)

        socket = zmq.Context().socket(zmq.PULL)
        socket.SNDTIMEO = SNDTIMEO
        socket.set_hwm(ZMQ_HWM)
        socket.setsockopt(zmq.LINGER, 3)

        socket.connect(HUNTER_ADDR)

        router = Client(remote=HUNTER_SINK_ADDR, token=self.token, nowait=True)

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        while not self.exit.is_set():
            data = []
            indicators = []

            try:
                s = dict(poller.poll(1000))
            except (KeyboardInterrupt, SystemExit):
                break

            if socket not in s:
                continue

            data = socket.recv_multipart()
            data = json.loads(data[0])

            logger.debug(data)

            if isinstance(data, dict):
                if not data.get('indicator'):
                    continue

                # searches
                if not data.get('itype'):
                    data = Indicator(
                        indicator=data['indicator'],
                        tags='search',
                        confidence=4,
                        group='everyone',
                        tlp='amber',
                    ).__dict__()

                if not data.get('tags'):
                    data['tags'] = []

            d = Indicator(**data)

            if d.indicator in ["", 'localhost', 'example.com']:
                continue

            if self.exclude.get(d.provider):
                for t in d.tags:
                    if t in self.exclude[d.provider]:
                        logger.debug('skipping: {}'.format(d.indicator))

            for p in plugins:
                try:
                    indicators = p.process(d)

                    indicators = [i.__dict__() for i in indicators]

                    if len(indicators) == 0:
                        continue

                    router.indicators_create(indicators)

                except Exception as e:
                    logger.error(e)
                    logger.error('[{}] giving up on: {}'.format(p, d))
                    if logger.getEffectiveLevel() == logging.DEBUG:
                        import traceback
                        traceback.print_exc()

        # socket.close()
        # router.close()


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            
        example usage:
            $ cif-hunter -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-router',
        parents=[p]
    )

    args = p.parse_args()
    setup_logging(args)
    logger = logging.getLogger(__name__)
    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    if args.logging_ignore:
        to_ignore = args.logging_ignore.split(',')

        for i in to_ignore:
            logging.getLogger(i).setLevel(logging.WARNING)

    setup_runtime_path(args.runtime_path)
    # setup_signals(__name__)

    h = Hunter()

    try:
        h.start()
    except KeyboardInterrupt or SystemExit:
        h.stop()


if __name__ == "__main__":
    main()
