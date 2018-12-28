# !/usr/bin/env python3

import logging
import os
import yaml
import ujson as json
import requests
import zmq
from zmq.eventloop import zmqstream, ioloop

from cif.constants import ROUTER_WEBHOOKS_ADDR
from cif.utils.manager import Manager as _Manager
from .utils.process import MyProcess

TRACE = os.getenv('CIF_WEBHOOK_TRACE', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if TRACE == '1':
    logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


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
            raise FileNotFoundError('missing webhooks.yml')

        with open('webhooks.yml') as f:
            try:
                self.hooks = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                logger.error(exc)

    @staticmethod
    def is_search(data):
        if data.get('indicator') and data.get('limit') \
                and data.get('nolog', '0') == '0':
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
            logger.info('no webhooks to send to... '
                        'is your webhooks.yml missing?')
            return

        data = json.loads(data[0])

        if not self.is_search(data):
            return

        for h in self.hooks:
            if h == 'slack':
                data = self._to_slack(data)

            if isinstance(data, dict):
                data = json.dumps(data)

            resp = requests.Session().post(self.hooks[h], data=data,
                                 headers={'Content-Type': 'application/json'},
                                 timeout=5)

            logger.debug(resp.status_code)
            if resp.status_code not in [200, 201]:
                logger.error(resp.text)

    def start(self):
        loop = ioloop.IOLoop()

        router = zmqstream.ZMQStream(zmq.Context().socket(zmq.PULL), loop)
        router.on_recv(self.send)
        router.connect(ROUTER_WEBHOOKS_ADDR)

        logger.debug('starting...')

        try:
            loop.start()

        except KeyboardInterrupt:
            # catch SIGINT
            pass

        except Exception as e:
            logger.error(e)

        self.stop()

