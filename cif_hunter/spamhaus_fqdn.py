
import logging
from pprint import pprint
import arrow
import os

from csirtg_indicator import Indicator

from cif.utils import resolve_ns
from .constants import ENABLED

CONFIDENCE = 9
PROVIDER = 'spamhaus.org'

CODES = {
    '127.0.1.2': {
        'tags': 'suspicious',
        'description': 'spammed domain',
    },
    '127.0.1.3': {
        'tags': 'suspicious',
        'description': 'spammed redirector / url shortener',
    },
    '127.0.1.4': {
        'tags': 'phishing',
        'description': 'phishing domain',
    },
    '127.0.1.5': {
        'tags': 'malware',
        'description': 'malware domain',
    },
    '127.0.1.6': {
        'tags': 'botnet',
        'description': 'Botnet C&C domain',
    },
    '127.0.1.102': {
        'tags': 'suspicious',
        'description': 'abused legit spam',
    },
    '127.0.1.103': {
        'tags': 'suspicious',
        'description': 'abused legit spammed redirector',
    },
    '127.0.1.104': {
        'tags': 'phishing',
        'description': 'abused legit phish',
    },
    '127.0.1.105': {
        'tags': 'malware',
        'description': 'abused legit malware',
    },
    '127.0.1.106': {
        'tags': 'botnet',
        'description': 'abused legit botnet',
    },
    '127.0.1.255': {
        'description': 'BANNED',
    },
}


def _resolve(data):
    data = '{}.dbl.spamhaus.org'.format(data)
    data = resolve_ns(data)
    if data and data[0]:
        return data[0]


def process(i):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    if i.provider == 'spamhaus.org':
        return

    r = _resolve(i.indicator)
    r = CODES.get(str(r), None)

    if not r:
        return

    confidence = CONFIDENCE
    if ' legit ' in r['description']:
        confidence = 6

    f = Indicator(**i.__dict__())

    f.tags = [r['tags']]
    f.description = r['description']
    f.confidence = confidence
    f.provider = PROVIDER
    f.reference_tlp = 'white'
    f.reference = 'http://www.spamhaus.org/query/dbl?domain={}'.format(f.indicator)
    f.lasttime = arrow.utcnow()
    return f
