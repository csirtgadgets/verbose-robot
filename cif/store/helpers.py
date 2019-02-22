
import arrow
from .constants import REQUIRED_ATTRIBUTES
from cifsdk.exceptions import AuthError
from base64 import b64decode


def _check_indicator(i, t):
    if not i.get('group'):
        i['group'] = t['groups'][0]

    if not i.get('provider'):
        i['provider'] = t['username']

    if not i.get('tags'):
        i['tags'] = 'suspicious'

    if not i.get('reported_at'):
        i['reported_at'] = arrow.utcnow().datetime

    for e in REQUIRED_ATTRIBUTES:
        if not i.get(e):
            raise ValueError('missing %s' % e)

    if i['group'] not in t['groups']:
        raise AuthError('unable to write to %s' % i['group'])

    return True


def _cleanup_indicator(i):
    if not i.get('message'):
        return

    try:
        i['message'] = b64decode(i['message'])
    except Exception as e:
        pass
