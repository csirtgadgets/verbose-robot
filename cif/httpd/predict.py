from flask_restplus import Namespace, Resource, reqparse, fields
from csirtg_domainsml_tf import predict as predict_domain
from csirtg_urlsml_tf import predict as predict_url
#from .whitelist import lookup as is_whitelisted
from csirtg_indicator.utils import resolve_itype

api = Namespace('predict', description='Predict related operations')

model = api.model('Prediction', {
    'data': fields.Integer(min=0, max=1),
    'message': fields.String,
})


@api.route('/')
@api.response(200, 'OK', model='Prediction')
class Predict(Resource):

    def is_whitelisted(self, i):
        return False

    @api.param('q', 'Query Prediction Interface')
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('q')
        args = parser.parse_args()

        if self.is_whitelisted(args.q):
            p = 0

        else:
            itype = resolve_itype(args.q)
            if not itype:
                api.abort(422)
                return

            if itype == 'fqdn':
                p = predict_domain(args.q)
            elif itype == 'url':
                p = predict_url(args.q)
            else:
                p = 0

            p = str(round((p[0][0] * 100), 2))

        return {'data': str(p)}
