import arrow
import abc
from cifsdk.exceptions import AuthError


class IndicatorManagerPlugin(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def search(self, token, filters, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, token, indicators, **kwargs):
        raise NotImplementedError

    def _check_token_groups(self, t, i):
        if not i.get('group'):
            raise ValueError('missing group')

        if i['group'] not in t['groups']:
            raise AuthError('unable to write to %s' % i['group'])

    def _timestamps_fix(self, i):
        if not i.get('last_at'):
            i['last_at'] = arrow.utcnow().datetime

        if not i.get('first_at'):
            i['first_at'] = i['last_at']

        if not i.get('reported_at'):
            i['reported_at'] = arrow.utcnow().datetime

    def _is_newer(self, i, rec):
        if not i.get('last_at'):
            return False

        i_last = arrow.get(i['last_at']).datetime
        rec_last = arrow.get(rec['last_at']).datetime

        if i_last > rec_last:
            return True
