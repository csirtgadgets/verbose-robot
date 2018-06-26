import logging
import requests
import time
import json
from pprint import pprint
from base64 import b64decode
import os
from time import sleep
import random

from cifsdk.exceptions import AuthError, TimeoutError, NotFound, SubmissionFailed, InvalidSearch, CIFBusy
from cifsdk.constants import VERSION, PYVERSION
from cifsdk.client import Client
from csirtg_indicator import Indicator

TRACE = os.environ.get('CIFSDK_CLIENT_HTTP_TRACE')
TIMEOUT = os.getenv('CIFSDK_CLIENT_HTTP_TIMEOUT', 120)
RETRIES = os.getenv('CIFSDK_CLIENT_HTTP_RETRIES', 5)
RETRIES_DELAY = os.getenv('CIFSDK_CLIENT_HTTP_RETRIES_DELAY', '30,60')

REMOTE = os.getenv('CIF_REMOTE', 'http://localhost:5000')
TOKEN = os.getenv('CIF_TOKEN')

if PYVERSION == 3:
    basestring = (str, bytes)

s, e = RETRIES_DELAY.split(',')
RETRIES_DELAY = random.uniform(int(s), int(e))

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

logger.setLevel(logging.WARNING)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)

if TRACE:
    logger.setLevel(logging.DEBUG)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.DEBUG)


class HTTP(Client):

    def __init__(self, remote=REMOTE, token=TOKEN, proxy=None, timeout=int(TIMEOUT), verify_ssl=True, **kwargs):
        if remote is None:
            remote = 'http://localhost:5000'

        if token is None:
            token = os.getenv('CIF_TOKEN')

        super(HTTP, self).__init__(remote, token, **kwargs)

        self.proxy = proxy
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.nowait = kwargs.get('nowait', False)

        self.session = requests.Session()
        self.session.headers["Accept"] = 'application/vnd.cif.v4+json'
        self.session.headers['User-Agent'] = 'cifsdk-py/{}'.format(VERSION)
        self.session.headers['Authorization'] = self.token
        self.session.headers['Accept-Encoding'] = 'deflate'

    def _check_status(self, resp, expect=200):
        if resp.status_code == expect:
            return

        if resp.status_code == 400:
            r = json.loads(resp.text)
            raise InvalidSearch(r['message'])

        if resp.status_code == 401:
            raise AuthError('unauthorized')

        if resp.status_code == 404:
            raise NotFound('not found')

        if resp.status_code == 408:
            raise TimeoutError('timeout')

        if resp.status_code == 422:
            msg = json.loads(resp.text)
            raise SubmissionFailed(msg['message'])

        if resp.status_code == 429:
            raise CIFBusy('RateLimit exceeded')

        if resp.status_code in [500, 501, 502, 503, 504]:
            raise CIFBusy('system seems busy..')

        if resp.status_code != expect:
            msg = 'unknown: %s' % resp.content
            raise RuntimeError(msg)

    def __get(self, uri, params):
        resp = self.session.get(uri, params=params, verify=self.verify_ssl, timeout=self.timeout)
        logger.debug(resp.text)
        n = RETRIES
        try:
            self._check_status(resp, expect=200)
            n = 0
            return resp
        except Exception as e:
            if resp.status_code == 429 or resp.status_code in [500, 501, 502, 503, 504]:
                logger.error(e)
            else:
                raise e

        for nn in (1, n):
            logger.warning('setting random retry interval to spread out the load')
            logger.warning('retrying in %.00fs' % RETRIES_DELAY)
            sleep(RETRIES_DELAY)

            resp = self.session.get(uri, params=params, verify=self.verify_ssl, timeout=self.timeout)
            if resp.status_code == 200:
                break

            if nn == n:
                raise CIFBusy('system seems busy.. try again later')

        return resp

    def _check_data(self, msgs):
        if isinstance(msgs, list):
            return msgs

        if msgs.get('status', False) not in ['success', 'failure']:
            raise RuntimeError(msgs)

        if msgs.get('status') == 'failure':
            raise InvalidSearch(msgs['message'])

        if msgs['data'] == '{}':
            msgs['data'] = []

        # check to see if it's straight elasticsearch json
        if isinstance(msgs['data'], basestring) and msgs['data'].startswith('{"hits":{"hits":[{"_source":'):
            msgs['data'] = json.loads(msgs['data'])
            msgs['data'] = [r['_source'] for r in msgs['data']['hits']['hits']]

        if not isinstance(msgs['data'], list):
            msgs['data'] = [msgs['data']]

        for m in msgs['data']:
            if not isinstance(m, dict):
                continue

            if not m.get('message'):
                continue

            try:
                m['message'] = b64decode(m['message'])
            except Exception as e:
                pass

        return msgs

    def _get(self, uri, params={}, retry=True):
        if not uri.startswith('http'):
            uri = "%s/%s/" % (self.remote, uri)

        resp = self.__get(uri, params)

        data = resp.content

        ss = (int(resp.headers['Content-Length']) / 1024 / 1024)
        logger.info('processing %.2f megs' % ss)

        msgs = json.loads(data.decode('utf-8'))

        msgs = self._check_data(msgs)
        return msgs

    def _post(self, uri, data, expect=201):
        if not uri.startswith('http'):
            uri = "%s/%s/" % (self.remote, uri)

        data = json.dumps(data)

        if self.nowait:
            uri = '{}?nowait=1'.format(uri)

        if isinstance(data, str):
            data = data.encode('utf-8')

        #TODO test? does this happen automagically?
        # data = zlib.compress(data)
        # headers = {
        #     'Content-Encoding': 'deflate',
        #     'Content-Type': 'application/json'
        # }

        headers = {'Content-Type': 'application/json'}
        logger.debug('submitting')
        resp = self.session.post(uri, data=data, verify=self.verify_ssl, headers=headers, timeout=self.timeout)
        logger.debug(resp.content)
        logger.debug(resp.status_code)
        n = RETRIES
        try:
            self._check_status(resp, expect=expect)
            n = 0
        except Exception as e:
            if resp.status_code == 429 or resp.status_code in [500, 501, 502, 503, 504]:
                logger.error(e)
            else:
                raise e

        while n != 0:
            logger.info('setting random retry interval to spread out the load')
            logger.info('retrying in %.00fs' % RETRIES_DELAY)
            sleep(RETRIES_DELAY)

            resp = self.session.post(uri, data=data, verify=self.verify_ssl, headers=headers, timeout=self.timeout)
            if resp.status_code in [200, 201]:
                break

            if n == 0:
                raise CIFBusy('system seems busy.. try again later')

        return json.loads(resp.content.decode('utf-8'))

    def _delete(self, uri, params={}):
        if not uri.startswith('http'):
            uri = "%s/%s/" % (self.remote, uri)

        params = {f: params[f] for f in params if params.get(f)}

        for f in ['nolog', 'limit']:
            if params.get(f):
                del params[f]

        resp = self.session.delete(uri, data=json.dumps(params), verify=self.verify_ssl, timeout=self.timeout)
        self._check_status(resp)
        return json.loads(resp.content.decode('utf-8'))

    def _patch(self, uri, data):
        if not uri.startswith('http'):
            uri = "%s/%s/" % (self.remote, uri)

        resp = self.session.patch(uri, data=json.dumps(data))
        self._check_status(resp)
        return json.loads(resp.content)

    def ping(self, write=False):
        t0 = time.time()
        rv = self._get('ping')
        if not rv:
            return

        rv = (time.time() - t0)
        logger.debug('return time: %.15f' % rv)
        return rv

    def ping_write(self):
        t0 = time.time()
        rv = self._post('ping', data=[], expect=200)
        if not rv:
            return

        rv = (time.time() - t0)
        logger.debug('return time: %.15f' % rv)
        return rv

    def graph_search(self, filters):
        return self._get('graph', params=filters)

    def stats_search(self, filters={}):
        return self._get('stats', params=filters)

    def indicators_search(self, filters):
        data = self._get('indicators', params=filters)

        # indicator v0 work-around
        # for i in data:
        #     i['reporttime'] = i.get('reported_at')
        #     i['firsttime'] = i.get('first_at')
        #     i['lasttime'] = i.get('last_at')
        #
        #     del i['reported_at']
        #     del i['first_at']
        #     del i['last_at']

        return data

    def indicators_create(self, data):
        if isinstance(data, Indicator):
            data = data.__dict__()

        if type(data) == dict:
            data = [data]

        if isinstance(data, list) and isinstance(data[0], Indicator):
            data = [i.__dict__() for i in data]

        # for i in data:
        #     if i == 'reporttime':
        #         data['reported_at'] = data[i]
        #         del data['reporttime']
        #
        #     if i == 'lasttime':
        #         data['lasttime'] = data[i]
        #         del data['lasttime']
        #
        #     if i == 'firsttime':
        #         data['first_at'] = data[i]
        #         del data['firsttime']

        rv = self._post('indicators', data)
        return rv["data"]

    def indicators_delete(self, filters):
        rv = self._delete('indicators', params=filters)
        return rv["data"]

    def tokens_search(self, filters):
        return self._get('tokens', params=filters)

    def tokens_delete(self, data):
        return self._delete('tokens', data)

    def tokens_create(self, data):
        return self._post('tokens', data)

    def tokens_edit(self, data):
        return self._patch('tokens', data)


Plugin = HTTP
