import logging, arrow
from csirtg_indicator import Indicator, resolve_itype
from urllib.parse import urlparse


logger = logging.getLogger('cif_hunter')


def process(i):
    if i.itype != 'url':
        return

    u = urlparse(i.indicator)
    if not u.hostname:
        return

    try:
        resolve_itype(u.hostname)
    except TypeError as e:
        logger.error(u.hostname)
        logger.error(e)
        return

    fqdn = Indicator(**i.__dict__())
    fqdn.lasttime = arrow.utcnow()
    fqdn.indicator = u.hostname
    fqdn.itype = 'fqdn'
    fqdn.confidence = 2
    fqdn.rdata = i.indicator
    fqdn.probability = 0

    return fqdn
