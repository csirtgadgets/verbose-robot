import logging
from dns.resolver import Timeout
import arrow

from csirtg_indicator import resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator
from cifsdk.utils.network import resolve_ns
from csirtg_indicator import Indicator
import os
ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)


def process(i):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    try:
        r = resolve_ns(i.indicator, t='CNAME')
        if not r:
            return
    except Timeout:
        return

    rv = []

    for rr in r:
        # http://serverfault.com/questions/44618/is-a-wildcard-cname-dns-record-valid
        rr = str(rr).rstrip('.').lstrip('*.')
        if rr in ['', 'localhost']:
            continue

        fqdn = Indicator(**i.__dict__())
        fqdn.probability = 0
        fqdn.indicator = rr
        fqdn.lasttime = arrow.utcnow()

        try:
            resolve_itype(fqdn.indicator)
        except InvalidIndicator:
            return

        fqdn.itype = 'fqdn'
        fqdn.confidence = int(fqdn.confidence / 2) if fqdn.confidence >= 2 else 0
        rv.append(fqdn)

    return rv
