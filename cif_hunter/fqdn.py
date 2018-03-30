import logging
from cifsdk.utils.network import resolve_ns
from csirtg_indicator import Indicator
from dns.resolver import Timeout
from csirtg_indicator import resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator
import arrow
import os
import copy

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)


def is_subdomain(i):
    bits = i.split('.')
    if len(bits) > 2:
        return True


def process(i):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    if 'search' in i.tags:
        return

    try:
        r = resolve_ns(i.indicator)
        if not r:
            return
    except Timeout:
        return

    rv = []

    for rr in r:
        rr = str(rr)
        if rr in ["", 'localhost']:
            continue

        ip = Indicator(**i.__dict__())
        ip.lasttime = arrow.utcnow()

        ip.indicator = rr
        try:
            resolve_itype(ip.indicator)
        except InvalidIndicator:
            continue

        ip.itype = 'ipv4'
        ip.rdata = i.indicator
        ip.confidence = int((ip.confidence / 2)) if ip.confidence >= 2 else 0
        rv.append(ip)

        pdns = Indicator(**copy.deepcopy(i.__dict__()))

        # also create a passive dns tag
        pdns.tags = 'pdns'
        pdns.confidence = 10
        pdns.probability = 0
        rv.append(pdns)

    return rv
