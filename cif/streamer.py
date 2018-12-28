# !/usr/bin/env python3

import logging
import zmq
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from .utils.process import MyProcess
import os
from zmq.eventloop import zmqstream, ioloop

from cifsdk.utils import setup_runtime_path, setup_logging
from cif.utils import get_argument_parser
from cif.utils.manager import Manager as _Manager
from .constants import ROUTER_STREAM_ADDR, ROUTER_STREAM_ADDR_PUB

TRACE = os.getenv('CIF_STREAMER_TRACE', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)


class Manager(_Manager):

    def __init__(self, context, threads=1):
        _Manager.__init__(self, Streamer, threads)

        self.socket = context.socket(zmq.PUSH)
        self.socket.connect(ROUTER_STREAM_ADDR)


class Streamer(MyProcess):

    def __init__(self, **kwargs):
        MyProcess.__init__(self, **kwargs)

        self.publisher = None

    def send(self, message):
        for m in message:
            self.publisher.send(m)

    def start(self):
        loop = ioloop.IOLoop()
        context = zmq.Context()

        logger.debug(f"bindings {ROUTER_STREAM_ADDR_PUB}")
        self.publisher = context.socket(zmq.PUB)
        self.publisher.bind(ROUTER_STREAM_ADDR_PUB)

        logger.debug(f"connecting to router: {ROUTER_STREAM_ADDR}")
        router = zmqstream.ZMQStream(context.socket(zmq.PULL), loop)
        router.on_recv(self.send)

        router.bind(ROUTER_STREAM_ADDR)

        logger.debug("starting...")

        try:
            loop.start()

        except KeyboardInterrupt:
            # catch SIGINT from above..
            pass

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

    s.start()


if __name__ == "__main__":
    main()
