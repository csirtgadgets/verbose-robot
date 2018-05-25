import logging
from flask_restplus import Namespace, Resource
from flask import session, request
import traceback

from cifsdk.client.zmq import ZMQ as Client
from cifsdk.constants import ROUTER_ADDR
from cifsdk.exceptions import InvalidSearch, AuthError


logger = logging.getLogger('cif-httpd')

api = Namespace('stats', description='Stats related operations')


@api.route('/')
class StatList(Resource):

    def _pull(self, filters={}):
        try:
            r = Client(ROUTER_ADDR, session['token']).stats_search(filters)

        except InvalidSearch as e:
            return api.abort(400)

        except AuthError as e:
            return api.abort(401)

        except Exception as e:
            logger.error(e)
            if logger.getEffectiveLevel() == logging.DEBUG:
                traceback.print_exc()
            return api.abort(500)

        return r

    @api.doc('list_stats')
    @api.param('q', 'Stat to group by [provider|itype|indicator]')
    @api.param('limit', 'Results limit..')
    def get(self):
        filters = {
            'q': request.args.get('q'),
            'limit': request.args.get('limit', 10)
        }
        r = self._pull(filters)

        return r
