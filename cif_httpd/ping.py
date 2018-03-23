from flask_restplus import Namespace, Resource, fields
from flask import session
import time
from cifsdk_zmq import ZMQ as Client

from cifsdk.constants import ROUTER_ADDR
from cifsdk.exceptions import AuthError, TimeoutError
from pprint import pprint

api = Namespace('ping', description='Ping API')

indicator = api.model('Ping', {
    'write': fields.Boolean(required=False, description='Test WRITE access'),
})


@api.route('/')
@api.response(401, 'Unauthorized')
@api.response(200, 'OK')
class Ping(Resource):

    def _ping(self, write=False):
        try:
            if write:
                r = Client(ROUTER_ADDR, session['token']).ping_write()
            else:
                r = Client(ROUTER_ADDR, session['token']).ping()

        except TimeoutError:
            return api.abort(408)

        except AuthError:
            return api.abort(401)

        if not r:
            return api.abort(503)

        return {'status': 'success', 'data': time.time()}

    @api.doc('get_ping')
    def get(self):
        """Ping the router, see if it's responding to requests and test READ access"""

        return self._ping()

    @api.doc('post_ping')
    def post(self):
        """Ping the router, test for WRITE access"""

        return self._ping(write=True)
