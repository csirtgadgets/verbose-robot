from flask_restplus import Namespace, Resource, fields
import time
from cifsdk_zmq import Client

from cifsdk.constants import ROUTER_ADDR
from cifsdk.exceptions import AuthError

api = Namespace('ping', description='Ping API')

indicator = api.model('Ping', {
    'write': fields.Boolean(required=False, description='Test WRITE access'),
})


@api.route('/')
@api.response(401, 'Unauthorized')
@api.response(200, 'OK')
class Ping(Resource):

    def _ping(self, token, write=False):
        try:
            if write:
                r = Client(ROUTER_ADDR, token).ping_write()
            else:
                r = Client(ROUTER_ADDR, token).ping()

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

        # token = pull_token()
        token = ''

        return self._ping(token)

    @api.doc('post_ping')
    def post(self):
        """Ping the router, test for WRITE access"""

        token = ''
        return self._ping(token, write=True)
