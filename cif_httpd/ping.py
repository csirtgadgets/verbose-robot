from flask_restplus import Namespace, Resource, fields
import time

api = Namespace('ping', description='Ping API')

indicator = api.model('Ping', {
    'write': fields.Boolean(required=False, description='Test WRITE access'),
})


@api.route('/')
@api.response(401, 'Unauthorized')
@api.response(200, 'OK')
class Ping(Resource):
    @api.doc('get_ping')
    def get(self):
        """Ping the router, see if it's responding to requests and test READ access"""
        # api.abort(401)

        return {'status': 'success', 'data': time.time()}

        token = pull_token()

        # try:
        #     r = Client(ROUTER_ADDR, token).ping(write=write)
        #
        # except TimeoutError:
        #     return jsonify_unknown(msg='timeout', code=408)
        #
        # except AuthError:
        #     return jsonify_unauth()
        #
        # if not r:
        #     return jsonify_unknown(503)
        #
        # return jsonify_success(r)

    @api.doc('post_ping')
    def post(self):
        """Ping the router, test for WRITE access"""

        return {'status': 'success', 'data': time.time()}

        token = pull_token()
