from flask_restplus import Namespace, Resource, fields, reqparse
from flask import session

from cifsdk_zmq import ZMQ as Client
from cifsdk.constants import ROUTER_ADDR
from cifsdk.exceptions import AuthError, TimeoutError

from pprint import pprint

api = Namespace('tokens', description='Token related operations')

token = api.model('Token', {
    'id': fields.String(required=True, description='The token id'),
    'token': fields.String(required=True, description='The token'),
    'user': fields.String(required=True, description='user associated with the token'),
    'write': fields.Boolean(default=False),
    'read': fields.Boolean(default=True),
    'expires_at': fields.DateTime(description='set a key expiration date'),
})


def _success(data=[]):
    return {'status': 'success', 'data': data}


def _failure(msg='unknown', data=[]):
    return {'status': 'failure', 'message': msg, 'data': data}


@api.route('/')
@api.response(401, 'Unauthorized')
@api.response(200, 'OK')
class TokenList(Resource):
    @api.param('q', 'Search for token by username')
    @api.doc('list_tokens')
    @api.marshal_list_with(token)
    def get(self):
        """List all Tokens"""
        parser = reqparse.RequestParser()
        parser.add_argument('q')
        args = parser.parse_args()

        try:
            return Client(ROUTER_ADDR, session['token']).tokens_search(filters={'q': args.q})
        except TimeoutError:
            return api.abort(408)

        except AuthError:
            return api.abort(401)

        finally:
            return api.abort(400)

    @api.doc('create_tokens')
    @api.marshal_list_with(token, code=201, description='Token created')
    def post(self, data):
        """Create a Token"""
        return _success()


@api.route('/<id>')
@api.param('id', 'The token identifier')
@api.response(404, 'Token not found')
class Token(Resource):
    @api.doc('get_token')
    @api.marshal_with(token)
    def get(self, id):
        """Fetch a Token given its identifier"""

        try:
            return Client(ROUTER_ADDR, session['token']).tokens_search(filters={'token': id})
        except TimeoutError:
            return api.abort(408)

        except AuthError:
            return api.abort(401)

        finally:
            return api.abort(400)

    @api.doc('update_token')
    @api.marshal_with(token, code=200, description='Token updated')
    def post(self, data):
        """Update a Token"""
        return _success()

    @api.doc('delete_token')
    @api.response(204, 'Deleted')
    def delete(self, id):
        """Delete a Token given its identifier"""
        return _success()
