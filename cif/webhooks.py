# !/usr/bin/env python3

import ujson as json
import logging
import zmq
from .utils.process import MyProcess
import os
import yaml
import requests

from cif.constants import ROUTER_WEBHOOKS_ADDR

TRACE = os.getenv('CIF_WEBHOOK_TRACE', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

from cif.utils.manager import Manager as _Manager


class Manager(_Manager):

    def __init__(self, context, threads=1):
        _Manager.__init__(self, Webhooks, threads)

        self.socket = context.socket(zmq.PUSH)
        self.socket.bind(ROUTER_WEBHOOKS_ADDR)


class Webhooks(MyProcess):
    def __init__(self, **kwargs):
        MyProcess.__init__(self, **kwargs)

        if kwargs.get('test'):
            return

        if not os.path.exists('webhooks.yml'):
            logger.error('webhooks.yml file is missing...')
            return

        with open('webhooks.yml') as f:
            try:
                self.hooks = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                logger.error(exc)

    def is_search(self, data):
        if data.get('indicator') and data.get('limit') and data.get('nolog', '0') == '0':
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

        if len(self.hooks) == 0:
            logger.info('no webhooks to send to... is your webhooks.yml missing?')
            return

        if not self.is_search(data):
            return

        for h in self.hooks:
            if h == 'slack':
                data = self._to_slack(data)

            if isinstance(data, dict):
                data = json.dumps(data)

            resp = requests.post(self.hooks[h], data=data, headers={'Content-Type': 'application/json'}, timeout=5)
            logger.debug(resp.status_code)
            if resp.status_code not in [200, 201]:
                logger.error(resp.text)

    def start(self):
        context = zmq.Context()

        router = context.socket(zmq.PULL)
        router.connect(ROUTER_WEBHOOKS_ADDR)

        poller = zmq.Poller()
        poller.register(router, zmq.POLLIN)

        while not self.exit.is_set():
            try:
                s = dict(poller.poll(1000))
            except (SystemExit, KeyboardInterrupt):
                break

            if router not in s:
                continue

            data = router.recv_multipart()
            logger.debug('got data..')
            logger.debug(data)

            self.send(json.loads(data[0]))
