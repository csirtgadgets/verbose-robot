import logging
from csirtg_indicator.utils.network import resolve_ns
from csirtg_indicator import Indicator
from dns.resolver import Timeout
from csirtg_indicator import resolve_itype
import arrow
import os
import copy
from pprint import pprint

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)


def process(i):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
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
        except:
            continue

        ip.itype = 'ipv4'
        ip.rdata = i.indicator
        ip.confidence = 1
        ip.probability = 0
        rv.append(ip)

        pdns = Indicator(**copy.deepcopy(i.__dict__()))

        # also create a passive dns tag
        pdns.tags = 'pdns'
        pdns.confidence = 4
        pdns.probability = 0
        pdns.indicator = ip.indicator
        pdns.rdata = i.indicator
        rv.append(pdns)

    return rv
