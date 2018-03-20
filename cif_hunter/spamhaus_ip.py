import logging, os
from csirtg_indicator import Indicator
from csirtg_indicator.utils import is_ipv4_net
from cifsdk.utils.network import resolve_ns
from pprint import pprint
import arrow

CONFIDENCE = 9
PROVIDER = 'spamhaus.org'

CODES = {
    '127.0.0.2': {
        'tags': 'spam',
        'description': 'Direct UBE sources, spam operations & spam services',
    },
    '127.0.0.3': {
        'tags': 'spam',
        'description': 'Direct snowshoe spam sources detected via automation',
    },
    '127.0.0.4': {
        'tags': 'exploit',
        'description': 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
    },
    '127.0.0.5': {
        'tags': 'exploit',
        'description': 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
    },
    '127.0.0.6': {
        'tags': 'exploit',
        'description': 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
    },
    '127.0.0.7': {
        'tags': 'exploit',
        'description': 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
    },
    '127.0.0.9': {
        'tags': 'hijacked',
        'description': 'Spamhaus DROP/EDROP Data',
    },
}

from .constants import ENABLED


def _resolve(data):
    data = reversed(data.split('.'))
    data = '{}.zen.spamhaus.org'.format('.'.join(data))
    data = resolve_ns(data)
    if data and data[0]:
        return data[0]


def process(self, i):
    if not ENABLED:
        return

    if i.itype not in ['ipv4', 'ipv6']:
        return

    if i.provider == 'spamhaus.org' and not is_ipv4_net(i.indicator):
        return

    try:
        r = self._resolve(i.indicator)
    except Exception as e:
        return

    r = CODES.get(str(r), None)
    if not r:
        return

    f = Indicator(**i.__dict__())

    f.tags = [r['tags']]
    f.description = r['description']
    f.confidence = CONFIDENCE
    f.provider = PROVIDER
    f.reference_tlp = 'white'
    f.reference = 'http://www.spamhaus.org/query/bl?ip={}'.format(f.indicator)
    f.lasttime = arrow.utcnow()
    return f
