# !/usr/bin/env python

import ujson as json
import logging
import zmq
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import multiprocessing
import os
from pprint import pprint

from cifsdk.utils import setup_runtime_path, setup_logging, get_argument_parser
from .constants import ROUTER_STREAM_ADDR

TRACE = os.getenv('CIF_STREAMER_TRACE', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)


class Streamer(multiprocessing.Process):

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.exit = multiprocessing.Event()

    def terminate(self):
        self.exit.set()

    def stop(self):
        logger.info('shutting down')
        self.terminate()

    def start(self):
        context = zmq.Context()

        router = context.socket(zmq.PULL)
        publisher = context.socket(zmq.PUB)

        publisher.bind(ROUTER_STREAM_ADDR)
        router.connect(ROUTER_STREAM_ADDR)

        poller = zmq.Poller()
        poller.register(router, zmq.POLLIN)

        while not self.exit.is_set():
            try:
                s = dict(poller.poll(1000))
            except SystemExit or KeyboardInterrupt:
                break

            if router not in s:
                continue

            data = router.recv_multipart()

            logger.debug('got data..')
            logger.debug(data)

            logger.debug('sending..')
            publisher.send_multipart(data)

            data = json.loads(data[0])


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
