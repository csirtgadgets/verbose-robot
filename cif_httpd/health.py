import time
from flask_restplus import Namespace, Resource

from .constants import HTTPD_TOKEN, ROUTER_ADDR

api = Namespace('health', description='Health API')


@api.route('/')
@api.response(401, 'Unauthorized')
@api.response(200, 'OK')
class Health(Resource):
    @api.doc('get_health')
    def get(self):
        """Ping the backend with data, check real results.."""

        if not HTTPD_TOKEN:
            return {'status': 'success', 'data': time.time()}

        try:
            # r = Client(ROUTER_ADDR, HTTPD_TOKEN).ping()
            # r = Client(ROUTER_ADDR, HTTPD_TOKEN).indicators_search({'indicator': 'example.com', 'nolog': '1'})
            r = True

        except TimeoutError:
            return api.abort(408)

        # except AuthError:
        #     return api.abort(401)

        if not r:
            return api.abort(503)