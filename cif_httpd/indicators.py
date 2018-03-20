from flask_restplus import Namespace, Resource, fields

itypes = ['ipv4', 'ipv6', 'url', 'fqdn', 'sha1', 'sha256', 'sha512', 'email']
api = Namespace('indicators', description='Indicator related operations')

indicator = api.model('Indicator', {
    'id': fields.String(required=True, description='The indicator id'),
    'indicator': fields.String(required=True, description='The indicator'),
    'itype': fields.String(enum=itypes),
    'confidence': fields.Float(min=0, max=10),
    'provider': fields.String,
    'reporttime': fields.DateTime,
    'lasttime': fields.DateTime,
})


def _success(data=[]):
    return {'status': 'success', data: data}


def _failure(msg='unknown', data=[]):
    return {'status': 'failure', 'message': msg, 'data': data}


@api.route('/')
class IndicatorList(Resource):
    @api.param('q', 'An indicator to search for')
    @api.param('itype', 'The indicator identifier')
    @api.param('tags', 'The indicator identifier')
    @api.param('confidence', 'The indicator identifier')
    @api.param('reporttime', 'The indicator identifier')
    @api.param('feed', 'Return as an aggregated feed')
    @api.param('csv', 'Return as CSV')
    @api.param('whitelist', 'Apply whitelist')
    @api.doc('list_indicators')
    @api.marshal_list_with(indicator)
    def get(self):
        """List all indicators"""
        return _success()

    @api.doc('create_indicator(s)')
    @api.marshal_with(indicator, code=201, description='Indicator created')
    def put(self, data=[]):
        """Create an Indicator"""
        if isinstance(data, dict):
            data = [data]

        if len(data) == 0:
            return _failure('missing indicator')

        rv = []
        return _success(rv)


@api.route('/<id>')
@api.param('id', 'The indicator identifier')
@api.response(404, 'Indicator not found')
class Indicator(Resource):
    @api.doc('get_indicator')
    @api.marshal_with(indicator)
    def get(self, id):
        """Fetch an indicator given its identifier"""
        return _success()

    @api.doc('delete_indicator')
    def delete(self, id):
        """Delete an Indicator given its identifier"""
        return _success()
