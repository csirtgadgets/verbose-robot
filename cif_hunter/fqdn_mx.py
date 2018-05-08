import logging
from dns.resolver import Timeout
import re
from pprint import pprint
import arrow

from csirtg_indicator import resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator
from cifsdk.utils.network import resolve_ns
from csirtg_indicator import Indicator
import os
ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)


def process(i):
    return
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    if 'search' in i.tags:
        return

    try:
        r = resolve_ns(i.indicator, t='MX')
        if not r:
            return
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
        fqdn.probability = 0
        fqdn.indicator = rr.rstrip('.')
        fqdn.lasttime = arrow.utcnow()

        try:
            resolve_itype(fqdn.indicator)
        except InvalidIndicator as e:
            continue

        fqdn.itype = 'fqdn'
        fqdn.rdata = i.indicator
        fqdn.confidence = 0
        rv.append(fqdn)

    return rv
