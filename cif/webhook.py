# !/usr/bin/env python3

import ujson as json
import logging
import zmq
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import multiprocessing
import os
import yaml
import requests
from pprint import pprint

from cifsdk.utils import setup_runtime_path, setup_logging, get_argument_parser
from cif.constants import ROUTER_WEBHOOK_ADDR

TRACE = os.getenv('CIF_WEBHOOK_TRACE', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)


class Webhook(multiprocessing.Process):

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.exit = multiprocessing.Event()

        if not os.path.exists('webhooks2.yml'):
            logger.error('webhooks.yml file is missing...')
            return

        with open('webhooks.yml') as f:
            try:
                self.hooks = yaml.load(f)
            except yaml.YAMLError as exc:
                logger.error(exc)

    def terminate(self):
        self.exit.set()

    def stop(self):
        logger.info('shutting down')
        self.terminate()

    def is_search(self, data):
        if data.get('indicator') and data.get('limit'):
            return True

        if not data.get('tags'):
            return

        if 'search' in set(data['tags']):
            return True

    def _to_slack(self, data):
        return {
            'text': "search: %s" % data.get('indicator')
        }

    def send(self, data):

        if not self.is_search(data):
            return

        for h in self.hooks:
            if h == 'slack':
                data = self._to_slack(data)

            if isinstance(data, dict):
                data = json.dumps(data)

            resp = requests.post(self.hooks[h], data=data, headers={'Content-Type': 'application/json'}, timeout=5)
            logger.debug(resp.status_code)
            if resp.status_code != 200:
                logger.error(resp.text)

        logger.debug('sending..')

        # send request

    def start(self):
        context = zmq.Context()

        router = context.socket(zmq.PULL)
        router.connect(ROUTER_WEBHOOK_ADDR)

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

            self.send(json.loads(data[0]))


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

    s = Webhook()

    try:
        s.start()
    except KeyboardInterrupt:
        s.stop()


if __name__ == "__main__":
    main()
