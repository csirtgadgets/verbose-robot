import logging
from dns.resolver import Timeout
import re
from pprint import pprint
import arrow

from csirtg_indicator import resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator
from cif.utils import resolve_ns
from csirtg_indicator import Indicator
from .constants import ENABLED


def process(i):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    if 'search' in i.tags:
        return

    try:
        r = resolve_ns(i.indicator, t='MX')
    except Timeout:
        return

    rv = []

    for rr in r:
        rr = re.sub(r'^\d+ ', '', str(rr))
        rr = str(rr).rstrip('.')

        if rr in ["", 'localhost']:
            continue

        # 10
        if re.match('^\d+$', rr):
            continue

        fqdn = Indicator(**i.__dict__())
        fqdn.indicator = rr.rstrip('.')
        fqdn.lasttime = arrow.utcnow()

        try:
            resolve_itype(fqdn.indicator)
        except InvalidIndicator as e:
            continue

        fqdn.itype = 'fqdn'
        fqdn.rdata = i.indicator
        fqdn.confidence = (fqdn.confidence - 5) if fqdn.confidence >= 5 else 0
        rv.append(fqdn)

    return rv
