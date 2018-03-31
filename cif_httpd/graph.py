import logging
import arrow
import re
import traceback
import copy

from flask_restplus import Namespace, Resource, fields
from flask import request, session

from cif.constants import FEEDS_LIMIT, FEEDS_WHITELIST_LIMIT, HTTPD_FEED_WHITELIST_CONFIDENCE
from cifsdk.constants import ROUTER_ADDR, VALID_FILTERS
from cifsdk_zmq import ZMQ as Client
from cifsdk.exceptions import AuthError, TimeoutError, InvalidSearch, SubmissionFailed, CIFBusy
from pprint import pprint

logger = logging.getLogger('cif-httpd')

api = Namespace('graph', description='Graph related operations')

graph = api.model('Graph', {
    'data': fields.Arbitrary,
})


@api.route('/')
class GraphList(Resource):

    @api.doc('list_graph')
    def get(self):
        """List Graph Nodes"""
        try:
            r = Client(ROUTER_ADDR, session['token']).graph_search({})

        except InvalidSearch as e:
            return api.abort(400)

        except AuthError as e:
            return api.abort(401)

        except Exception as e:
            logger.error(e)
            if logger.getEffectiveLevel() == logging.DEBUG:
                traceback.print_exc()
            return api.abort(500)

        return {'status': 'success', 'data': r }, 200
