import logging

from flask_restplus import Namespace, Resource, fields
from flask import request, session

from cifsdk.constants import ROUTER_ADDR, VALID_FILTERS
from cifsdk_zmq import ZMQ as Client
from cifsdk.exceptions import AuthError, TimeoutError, InvalidSearch, SubmissionFailed, CIFBusy
from pprint import pprint

CONFIDENCE_DEFAULT = 7

logger = logging.getLogger('cif-httpd')

itypes = ['ipv4', 'ipv6', 'url', 'fqdn', 'sha1', 'sha256', 'sha512', 'email']
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
    'probability': fields.Float,
    'portlist': fields.String,
    'protocol': fields.String,
    'expire_at': fields.DateTime,
    'ttl': fields.Float(description='Time To Live [Days- use decimal for hours, minutes, etc]')
})

envelope = api.model('Envelope', {
    'data': fields.Arbitrary,
    'message': fields.String,
})


def _success(data=[]):
    return {'status': 'success', 'data': data}


def _failure(msg='unknown', data=[]):
    return {'status': 'failure', 'message': msg, 'data': data}


@api.route('/')
class IndicatorList(Resource):

    def _pull_feed(self, filters):
        try:
            r = Client(ROUTER_ADDR, session['token']).indicators_search(filters)

        except RuntimeError as e:
            logger.error(e)
            return api.abort(422)

        except InvalidSearch as e:
            return api.abort(400)

        except AuthError:
            return api.abort(401)

        except Exception as e:
            logger.error(e)
            return api.abort(503)

        return r


    def _pull_whitelist(self):


    @api.param('q', 'An indicator to search for')
    @api.param('itype', 'The indicator identifier')
    @api.param('tags', 'The indicator identifier')
    @api.param('confidence', 'The indicator identifier')
    @api.param('reported_at', 'The indicator identifier')
    @api.param('probability')
    @api.param('nofeed', 'Return as an aggregated feed')
    @api.doc('list_indicators')
    def get(self):
        """List all indicators"""
        filters = {}
        for f in VALID_FILTERS:
            if request.args.get(f):
                filters[f] = request.args.get(f)

        if request.args.get('q'):
            filters['indicator'] = request.args.get('q')

        if not filters.get('indicator') and not filters.get('tags') and not filters.get('itype'):
            return {'message': 'indicator OR (tags AND itype) params required'}, 403

        if not filters.get('confidence'):
            filters['confidence'] = CONFIDENCE_DEFAULT

        logger.debug(filters)

        r = self._pull_feed(filters)

        if not request.args.get('nofeed', '0') == '0':
            return r, 200

        wl = self._pull_feed(filters)

        return r, 200

    @api.doc('create_indicator(s)')
    @api.param('nowait', 'Submit but do not wait for a response')
    @api.marshal_with(envelope, code=201, description='Indicator created')
    def post(self):
        """Create an Indicator"""
        if len(request.data) == 0:
            return 'missing indicator', 422

        fireball = False
        nowait = request.args.get('nowait', False)

        if request.headers.get('Content-Length'):
            if int(request.headers['Content-Length']) > 5000:
                fireball = True
        try:
            r = Client(ROUTER_ADDR, session['token']).indicators_create(request.data, nowait=nowait, fireball=fireball)
            if nowait:
                r = {'message': 'pending'}

        except SubmissionFailed as e:
            logger.error(e)
            return api.abort(422)

        except RuntimeError as e:
            logger.error(e)
            return api.abort(422)

        except TimeoutError as e:
            return api.abort(408)

        except CIFBusy:
            return api.abort(503)

        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()
            return api.abort(422)

        except AuthError:
            return api.abort(401)

        return {'data': r, 'message': 'success'}, 201


# @api.route('/<id>')
# @api.param('id', 'The indicator identifier')
# @api.response(404, 'Indicator not found')
# class Indicator(Resource):
#     @api.doc('get_indicator')
#     @api.marshal_with(indicator)
#     def get(self, id):
#         """Fetch an indicator given its identifier"""
#         return _success()
#
#     @api.doc('delete_indicator')
#     def delete(self, id):
#         """Delete an Indicator given its identifier"""
#         return _success()
