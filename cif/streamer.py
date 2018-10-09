# !/usr/bin/env python3

import ujson as json
import logging
import zmq
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from .utils.process import MyProcess
import os

from cifsdk.utils import setup_runtime_path, setup_logging
from cif.utils import get_argument_parser
from .constants import ROUTER_STREAM_ADDR, ROUTER_STREAM_ADDR_PUB

TRACE = os.getenv('CIF_STREAMER_TRACE', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)


class Streamer(MyProcess):

    def __init__(self, **kwargs):
        MyProcess.__init__(self, **kwargs)

    def start(self):
        context = zmq.Context()

        router = context.socket(zmq.PULL)
        publisher = context.socket(zmq.PUB)

        logger.debug('binding: %s' % ROUTER_STREAM_ADDR_PUB)
        publisher.bind(ROUTER_STREAM_ADDR_PUB)

        logger.debug('connecting: %s' % ROUTER_STREAM_ADDR)
        router.connect(ROUTER_STREAM_ADDR)

        poller = zmq.Poller()
        poller.register(router, zmq.POLLIN)

        logger.info('streamer started..')
        while not self.exit.is_set():
            try:
                s = dict(poller.poll(1000))
            except (SystemExit, KeyboardInterrupt):
                break

            if router not in s:
                continue

            data = router.recv_multipart()

            logger.debug(data)

            logger.debug('sending..')
            for d in data:
                publisher.send(d)

        router.close()
        publisher.close()
        context.term()
        del router
        self.stop()


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CIF_ROUTER_STREAM_ADDR
            CIF_STREAM_ADDR

        example usage:
            $ cif-streamer -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif-streamer',
        parents=[p]
    )

    args = p.parse_args()
    setup_logging(args)

    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    setup_runtime_path(args.runtime_path)
    # setup_signals(__name__)

    s = Streamer()

    try:
        s.start()
    except KeyboardInterrupt:
        s.stop()


if __name__ == "__main__":
    main()
