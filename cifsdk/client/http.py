import logging
import requests
import time
import json
from cifsdk.exceptions import AuthError, TimeoutError, NotFound, SubmissionFailed, InvalidSearch, CIFBusy
from cifsdk.constants import VERSION, PYVERSION
from pprint import pprint
from base64 import b64decode
from cifsdk.client import Client
import os
import zlib
from time import sleep
import random

if PYVERSION == 3:
    basestring = (str, bytes)


requests.packages.urllib3.disable_warnings()

TRACE = os.environ.get('CIFSDK_CLIENT_HTTP_TRACE')
TIMEOUT = os.getenv('CIFSDK_CLIENT_HTTP_TIMEOUT', 120)
RETRIES = os.getenv('CIFSDK_CLIENT_HTTP_RETRIES', 5)
RETRIES_DELAY = os.getenv('CIFSDK_CLIENT_HTTP_RETRIES_DELAY', '30,60')

s, e = RETRIES_DELAY.split(',')
RETRIES_DELAY = random.uniform(int(s), int(e))

logger = logging.getLogger(__name__)

logger.setLevel(logging.WARNING)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)

if TRACE:
    logger.setLevel(logging.DEBUG)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.DEBUG)


class HTTP(Client):

    def __init__(self, remote, token, proxy=None, timeout=int(TIMEOUT), verify_ssl=True, **kwargs):
        super(HTTP, self).__init__(remote, token, **kwargs)

        self.proxy = proxy
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.nowait = kwargs.get('nowait', False)

        self.session = requests.Session()
        self.session.headers["Accept"] = 'application/vnd.cif.v3+json'
        self.session.headers['User-Agent'] = 'cifsdk-py/{}'.format(VERSION)
        self.session.headers['Authorization'] = 'Token token=' + self.token
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Accept-Encoding'] = 'deflate'

    def _check_status(self, resp, expect=200):
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

    def _get(self, uri, params={}, retry=True):
        if not uri.startswith('http'):
            uri = self.remote + uri

        resp = self.session.get(uri, params=params, verify=self.verify_ssl, timeout=self.timeout)
        n = RETRIES
        try:
            self._check_status(resp, expect=200)
            n = 0
        except Exception as e:
            if resp.status_code == 429 or resp.status_code in [500, 501, 502, 503, 504]:
                logger.error(e)
            else:
                raise e

        while n != 0:
            logger.warning('setting random retry interval to spread out the load')
            logger.warning('retrying in %.00fs' % RETRIES_DELAY)
            sleep(RETRIES_DELAY)

            resp = self.session.get(uri, params=params, verify=self.verify_ssl, timeout=self.timeout)
            if resp.status_code == 200:
                break

            if n == 0:
                raise CIFBusy('system seems busy.. try again later')

        data = resp.content

        s = (int(resp.headers['Content-Length']) / 1024 / 1024)
        logger.info('processing %.2f megs' % s)

        msgs = json.loads(data.decode('utf-8'))

        if msgs['data'] == '{}':
            msgs['data'] = []

        if isinstance(msgs['data'], basestring) and msgs['data'].startswith('{"hits":{"hits":[{"_source":'):
            msgs['data'] = json.loads(msgs['data'])
            msgs['data'] = [r['_source'] for r in msgs['data']['hits']['hits']]

        if not msgs.get('status') and not msgs.get('message') == 'success':
            raise RuntimeError(msgs)

        if msgs.get('status') and msgs['status'] == 'failure':
            raise InvalidSearch(msgs['message'])

        if isinstance(msgs.get('data'), list):
            for m in msgs['data']:
                if m.get('message'):
                    try:
                        m['message'] = b64decode(m['message'])
                    except Exception as e:
                        pass
        return msgs

    def _post(self, uri, data):
        if type(data) == dict:
            data = json.dumps(data)

        if self.nowait:
            uri = '{}?nowait=1'.format(uri)

        if isinstance(data, str):
            data = data.encode('utf-8')

        data = zlib.compress(data)
        headers = {
            'Content-Encoding': 'deflate'
        }
        resp = self.session.post(uri, data=data, verify=self.verify_ssl, headers=headers, timeout=self.timeout)

        logger.debug(resp.content)
        n = RETRIES
        try:
            self._check_status(resp, expect=201)
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
        params = {f: params[f] for f in params if params.get(f)}
        if params.get('nolog'):
            del params['nolog']

        if params.get('limit'):
            del params['limit']

        resp = self.session.delete(uri, data=json.dumps(params), verify=self.verify_ssl, timeout=self.timeout)
        self._check_status(resp)
        return json.loads(resp.content.decode('utf-8'))

    def _patch(self, uri, data):
        resp = self.session.patch(uri, data=json.dumps(data))
        self._check_status(resp)
        return json.loads(resp.content)

    def indicators_search(self, filters):
        rv = self._get('/search', params=filters)
        return rv['data']

    def indicators_create(self, data):
        data = str(data).encode('utf-8')

        uri = "{0}/indicators".format(self.remote)
        logger.debug(uri)
        rv = self._post(uri, data)
        return rv["data"]

    def indicators_delete(self, filters):
        uri = "{0}/indicators".format(self.remote)
        logger.debug(uri)
        rv = self._delete(uri, params=filters)
        return rv["data"]

    def feed(self, filters):
        rv = self._get('/feed', params=filters)
        return rv['data']

    def ping(self, write=False):
        t0 = time.time()

        uri = '/ping'
        if write:
            uri = '/ping?write=1'

        rv = self._get(uri)

        if rv:
            rv = (time.time() - t0)
            logger.debug('return time: %.15f' % rv)

        return rv

    def tokens_search(self, filters):
        rv = self._get('{}/tokens'.format(self.remote), params=filters)
        return rv['data']

    def tokens_delete(self, data):
        rv = self._delete('{}/tokens'.format(self.remote), data)
        return rv['data']

    def tokens_create(self, data):
        logger.debug(data)
        rv = self._post('{}/tokens'.format(self.remote), data)
        return rv['data']

    def tokens_edit(self, data):
        rv = self._patch('{}/tokens'.format(self.remote), data)
        return rv['data']


Plugin = HTTP
