import logging
from dns.resolver import Timeout
import arrow

from csirtg_indicator import resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator
from cifsdk.utils.network import resolve_ns
from csirtg_indicator import Indicator
from .constants import ENABLED


def process(self, i, router):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    try:
        r = resolve_ns(i.indicator, t='CNAME')
    except Timeout:
        return

    rv = []

    for rr in r:
        # http://serverfault.com/questions/44618/is-a-wildcard-cname-dns-record-valid
        rr = str(rr).rstrip('.').lstrip('*.')
        if rr in ['', 'localhost']:
            continue

        fqdn = Indicator(**i.__dict__())
        fqdn.indicator = rr
        fqdn.lasttime = arrow.utcnow()

        try:
            resolve_itype(fqdn.indicator)
        except InvalidIndicator:
            return

        fqdn.itype = 'fqdn'
        fqdn.confidence = (fqdn.confidence - 1)
        rv.append(fqdn)

    return rv
