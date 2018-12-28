#!/usr/bin/env python3

import ujson as json
import logging
import traceback
import zmq
import os
from time import time
from pprint import pprint

from csirtg_indicator import Indicator

from cif.utils.predict import predict_fqdns, predict_ips, predict_urls
from cif.utils.process import MyProcess
from cif.constants import GATHERER_ADDR, GATHERER_SINK_ADDR
from cifsdk.msg import Msg
from cifsdk.utils import load_plugins
import cif.gatherer
from cif.manager import Manager as _Manager


RESOLVE_PEERS = os.getenv('CIF_GATHERER_PEERS', False)
if RESOLVE_PEERS == '1':
    RESOLVE_PEERS = True

SNDTIMEO = 30000
LINGER = 0
TRACE = os.environ.get('CIF_GATHERER_TRACE')

PREDICT = os.getenv('CIF_GATHERER_PREDICT', '1')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE:
    logger.setLevel(logging.DEBUG)


class Manager(_Manager):

    def __init__(self, context, threads=2):
        _Manager.__init__(self, Gatherer, threads)

        self.s = context.socket(zmq.PUSH)
        self.s.bind(GATHERER_ADDR)

        self.sink_s = context.socket(zmq.PULL)
        self.sink_s.bind(GATHERER_SINK_ADDR)


class Gatherer(MyProcess):
    def __init__(self, pull=GATHERER_ADDR, push=GATHERER_SINK_ADDR, **kwargs):
        MyProcess.__init__(self)
        self.pull = pull
        self.push = push

        self.gatherers = load_plugins(cif.gatherer.__path__)

    def process(self, data):
        if isinstance(data, dict):
            data = [data]

        s = time()
        indicators = [Indicator(**d, resolve_geo=True, resolve_peers=RESOLVE_PEERS) for d in data]
        for g in self.gatherers:
            for i in indicators:
                try:
                    g.process(i)
                except Exception as e:
                    from pprint import pprint
                    pprint(i)

                    logger.error('gatherer failed: %s' % g)
                    logger.error(e)
                    traceback.print_exc()

        # these should be done in bulk
        if PREDICT == '1':
            try:
                indicators = predict_urls(indicators)
                indicators = predict_fqdns(indicators)
                indicators = predict_ips(indicators)
            except Exception as e:
                logger.error('predictions failed')
                logger.error(e)
                traceback.print_exc()

        logger.debug('done: %f' % (time() - s))
        return [i.__dict__() for i in indicators]

    def start(self):
        context = zmq.Context()
        pull_s = context.socket(zmq.PULL)
        push_s = context.socket(zmq.PUSH)

        push_s.SNDTIMEO = SNDTIMEO
        push_s.setsockopt(zmq.LINGER, 3)
        pull_s.setsockopt(zmq.LINGER, 3)

        pull_s.connect(self.pull)
        push_s.connect(self.push)

        logger.info('connected')

        poller = zmq.Poller()
        poller.register(pull_s)

        while not self.exit.is_set():
            try:
                s = dict(poller.poll(1000))
            except (KeyboardInterrupt, SystemExit):
                break

            if pull_s not in s:
                continue

            id, token, mtype, data = Msg().recv(pull_s)

            data = json.loads(data)

            data = self.process(data)
            Msg(id=id, mtype=mtype, token=token, data=data).send(push_s)


def main():
    g = Gatherer()

    data = [{"indicator": "128.205.1.1"}, {'indicator': '128.205.1.2'}, {'indicator': '54.165.246.0/24'}]
    data = g.process(data)
    pprint(data)


if __name__ == '__main__':
    main()
