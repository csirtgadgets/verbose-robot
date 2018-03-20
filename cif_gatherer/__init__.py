#!/usr/bin/env python

import ujson as json
import logging
import traceback
import zmq
import multiprocessing
from cifsdk_msg import Msg
import os
import cif.gatherer
from cif.constants import GATHERER_ADDR, GATHERER_SINK_ADDR
from csirtg_indicator import Indicator
import time
from pprint import pprint

SNDTIMEO = 30000
LINGER = 0

logger = logging.getLogger(__name__)
TRACE = os.environ.get('CIF_GATHERER_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if TRACE:
    logger.setLevel(logging.DEBUG)


class Gatherer(multiprocessing.Process):

    def __init__(self, pull=GATHERER_ADDR, push=GATHERER_SINK_ADDR):
        multiprocessing.Process.__init__(self)
        self.pull = pull
        self.push = push
        self.exit = multiprocessing.Event()

        self._init_plugins()

    def _init_plugins(self):
        import pkgutil
        self.gatherers = []
        logger.debug('loading plugins...')
        for loader, modname, is_pkg in pkgutil.iter_modules(cif.gatherer.__path__, 'cif_gatherer.'):
            p = loader.find_module(modname).load_module(modname)
            self.gatherers.append(p)
            logger.debug('plugin loaded: {}'.format(modname))

    def terminate(self):
        self.exit.set()

    def process(self, data):
        rv = []
        if isinstance(data, dict):
            data = [data]

        for d in data:
            i = Indicator(**d)

            for g in self.gatherers:
                try:
                    g.process(i)
                except Exception as e:
                    from pprint import pprint
                    pprint(i)

                    logger.error('gatherer failed: %s' % g)
                    logger.error(e)
                    traceback.print_exc()

            rv.append(i.__dict__())

        return rv

    def start(self):
        context = zmq.Context()
        pull_s = context.socket(zmq.PULL)
        push_s = context.socket(zmq.PUSH)

        push_s.SNDTIMEO = SNDTIMEO

        logger.debug('connecting to sockets...')
        pull_s.connect(self.pull)
        push_s.connect(self.push)
        logger.debug('starting Gatherer')

        poller = zmq.Poller()
        poller.register(pull_s)

        while not self.exit.is_set():
            try:
                s = dict(poller.poll(1000))
            except Exception as e:
                self.logger.error(e)
                break

            if pull_s not in s:
                continue

            id, token, mtype, data = Msg().recv(pull_s)

            data = json.loads(data)

            start = time.time()
            data = self.process(data)
            data = json.dumps(data)
            logger.debug('sending back to router: %f' % (time.time() - start))
            Msg(id=id, mtype=mtype, token=token, data=data).send(push_s)

        logger.info('shutting down gatherer..')


def main():
    g = Gatherer()

    data = {"indicator": "example.com"}
    data = g.process(data)
    pprint(data)


if __name__ == '__main__':
    main()
