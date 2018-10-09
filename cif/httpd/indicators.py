import logging
import arrow
import re
import traceback
import copy

from flask_restplus import Namespace, Resource, fields
from flask import request, session, current_app

from cif.constants import FEEDS_LIMIT, FEEDS_WHITELIST_LIMIT, HTTPD_FEED_WHITELIST_CONFIDENCE
from cifsdk.constants import ROUTER_ADDR, VALID_FILTERS
from cifsdk.client.zmq import ZMQ as Client
from cifsdk.exceptions import AuthError, TimeoutError, InvalidSearch, SubmissionFailed, CIFBusy
import zmq
from pprint import pprint


# TODO- into csirtg_indicator
from csirtg_indicator.feed import aggregate
from csirtg_indicator.feed import process as feed
from csirtg_indicator.feed.fqdn import process as feed_fqdn
from csirtg_indicator.feed.ipv4 import process as feed_ipv4
from csirtg_indicator.feed.ipv6 import process as feed_ipv6

FEED_PLUGINS = {
    'ipv4': feed_ipv4,
    'ipv6': feed_ipv6,
    'fqdn': feed_fqdn,
    'url': feed,
    'email': feed,
    'md5': feed,
    'sha1': feed,
    'sha256': feed,
    'sha512': feed,
    'asn': feed,
}

DAYS_SHORT = 21
DAYS_MEDIUM = 60
DAYS_LONG = 90
DAYS_REALLY_LONG = 180

FEED_DAYS = {
    'ipv4': DAYS_SHORT,
    'ipv6': DAYS_SHORT,
    'url': DAYS_MEDIUM,
    'email': DAYS_MEDIUM,
    'fqdn': DAYS_MEDIUM,
    'md5': DAYS_MEDIUM,
    'sha1': DAYS_MEDIUM,
    'sha256': DAYS_MEDIUM,
    'asn': DAYS_MEDIUM,
}


CONFIDENCE_DEFAULT = 3


# http://stackoverflow.com/a/456747
def feed_factory(name):
    return FEED_PLUGINS.get(name, None)


logger = logging.getLogger('cif-httpd')

itypes = ['ipv4', 'ipv6', 'url', 'fqdn', 'sha1', 'sha256', 'sha512', 'email', 'asn']

api = Namespace('indicators', description='Indicator related operations')


indicator = api.model('Indicator', {
    'id': fields.String(required=True, description='The indicator id'),
    'indicator': fields.String(required=True, description='The indicator'),
    'itype': fields.String(enum=itypes),
    'confidence': fields.Float(min=0, max=10),
    'provider': fields.String(required=True),
    'groups': fields.List(fields.String),
    'tlp': fields.String(enum=['white', 'green', 'amber', 'red']),
    'reported_at': fields.DateTime,
    'last_at': fields.DateTime(required=True),
    'first_at': fields.DateTime,
    'probability': fields.Float(min=0, max=100),
    'portlist': fields.String,
    'protocol': fields.String,
    'expire_at': fields.DateTime,
    'ttl': fields.Float(description='Time To Live [Days- use decimal for hours, minutes, etc]')
})

envelope = api.model('Envelope', {
    'data': fields.Arbitrary,
    'message': fields.String,
})


@api.route('/')
class IndicatorList(Resource):

    def _pull(self, filters):
        try:
            r = Client(ROUTER_ADDR, session['token']).indicators_search(filters)

        except InvalidSearch as e:
            return api.abort(400)

        except AuthError as e:
            return api.abort(401)

        except zmq.error.Again as e:
            return api.abort(503)

        except Exception as e:
            logger.error(e)
            if logger.getEffectiveLevel() == logging.DEBUG:
                traceback.print_exc()
            return api.abort(500)

        return r

    def _pull_feed(self, filters, agg=True):
        if agg and not filters.get('reported_at') and not filters.get('days') and not filters.get('hours'):
            if not filters.get('itype'):
                filters['days'] = str(DAYS_SHORT)
            else:
                filters['days'] = str(FEED_DAYS[filters['itype']])

        if agg and not filters.get('reported_at'):
            if filters.get('days'):
                if re.match(r'^\d+$', filters['days']):
                    now = arrow.utcnow()
                    end = '{0}Z'.format(now.format('YYYY-MM-DDTHH:mm:ss'))
                    now = now.replace(days=-int(filters['days']))
                    start = '{0}Z'.format(now.format('YYYY-MM-DDTHH:mm:ss'))
                    filters['reported_at'] = '%s,%s' % (start, end)
                del filters['days']

            if filters.get('hours'):
                if re.match(r'^\d+$', filters['hours']):
                    now = arrow.utcnow()
                    end = '{0}Z'.format(now.format('YYYY-MM-DDTHH:mm:ss'))
                    now = now.replace(hours=-int(filters['hours']))
                    start = '{0}Z'.format(now.format('YYYY-MM-DDTHH:mm:ss'))
                    filters['reported_at'] = '%s,%s' % (start, end)
                del filters['hours']

            if filters.get('today'):
                if filters['today'] == '1':
                    now = arrow.utcnow()
                    start = '{0}Z'.format(now.format('YYYY-MM-DDT00:00:00'))
                    end = '{0}Z'.format(now.format('YYYY-MM-DDT23:59:59'))
                    filters['reported_at'] = '%s,%s' % (start, end)
                del filters['today']

        if not filters.get('limit'):
            filters['limit'] = FEEDS_LIMIT

        if agg:
            return aggregate(self._pull(filters))

        return self._pull(filters)

    def _pull_whitelist(self, filters={}):
        wl_filters = copy.deepcopy(filters)

        # whitelists are typically updated 1/month so we should catch those
        # esp for IP addresses
        wl_filters['tags'] = 'whitelist'
        wl_filters['confidence'] = HTTPD_FEED_WHITELIST_CONFIDENCE

        wl_filters['nolog'] = '1'
        wl_filters['limit'] = FEEDS_WHITELIST_LIMIT

        return aggregate(self._pull(wl_filters))

    def _filters_cleanup(self):
        filters = {}
        for f in VALID_FILTERS:
            if request.args.get(f):
                filters[f] = request.args.get(f)

        if request.args.get('q'):
            filters['indicator'] = request.args.get('q')

        if not filters.get('confidence') \
                and not filters.get('no_feed', '0') == '1' and not filters.get('indicator'):
            filters['confidence'] = CONFIDENCE_DEFAULT

        return filters

    @api.param('q', 'An indicator to search for')
    @api.param('itype', 'The indicator identifier')
    @api.param('tags', 'The indicator identifier')
    @api.param('confidence', 'The indicator identifier')
    @api.param('probability')
    @api.param('reported_at', 'The indicator identifier')
    @api.param('today')
    @api.param('hours')
    @api.param('days')
    @api.param('nofeed', 'TBD')
    @api.param('fmt', 'Return format, default csv [json|csv]')
    @api.doc('list_indicators')
    def get(self):
        """List all indicators"""
        filters = self._filters_cleanup()

        logger.debug(filters)

        if not filters.get('indicator') and not filters.get('tags') and not filters.get('itype'):
            return {'message': 'q OR tags|itype params required'}, 400

        if current_app.config.get('dummy'):
            return {'status': 'success', 'data': [{'indicator': filters['indicator']}]}

        if filters.get('indicator') or filters.get('no_feed', '0') == '1':
            if filters.get('no_feed'):
                del filters['no_feed']
            return self._pull_feed(filters, agg=False), 200

        f = feed_factory(filters['itype'])

        tags = set([filters.get('tags')])
        if 'whitelist' in tags:
            return self._pull_feed(filters), 200

        myfeed = list(f(
            self._pull_feed(filters),
            self._pull_whitelist(filters)
        ))

        myfeed = aggregate(myfeed)

        # https://github.com/noirbizarre/flask-restplus/blob/d4bd1847ae607d3c6c1b3b4fedfc6402e961b9e6/flask_restplus/api.py#L326
        if 'text/plain' in request.headers.get('Accept'):
            from csirtg_indicator.format.csv import get_lines
            csv = ''
            for l in get_lines(myfeed):
                csv += l + "\n"

            return csv, 200

        return myfeed, 200

    @api.doc('create_indicator(s)')
    @api.param('nowait', 'Submit but do not wait for a response')
    @api.response(201, 'success', model='Envelope')
    def post(self):
        """Create an Indicator"""
        if len(request.data) == 0:
            return 'missing indicator', 422

        fireball = False
        nowait = request.args.get('nowait', False)

        if request.headers.get('Content-Length'):

            logger.debug('size: %0.2f kb' % (float(request.headers['Content-Length']) / 1024))
            if int(request.headers['Content-Length']) > 5000:
                fireball = True
        try:
            r = Client(ROUTER_ADDR, session['token']).indicators_create(request.data, nowait=nowait, fireball=fireball)
            if nowait:
                r = {'message': 'pending'}

        except SubmissionFailed as e:
            logger.error(e)
            return api.abort(422)

        except TimeoutError as e:
            return api.abort(408)

        except CIFBusy:
            return api.abort(503)

        except AuthError:
            return api.abort(401)

        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()
            return api.abort(400)

        return {'data': r, 'message': 'success'}, 201
