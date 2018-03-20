import logging, arrow

from csirtg_indicator import Indicator, resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


logger = logging.getLogger('cif_hunter')


def process(i):
    if i.itype != 'url':
        return

    u = urlparse(i.indicator)
    if not u.hostname:
        return

    try:
        resolve_itype(u.hostname)
    except InvalidIndicator as e:
        logger.error(u.hostname)
        logger.error(e)
        return

    fqdn = Indicator(**i.__dict__())
    fqdn.lasttime = arrow.utcnow()
    fqdn.indicator = u.hostname
    fqdn.itype = 'fqdn'
    fqdn.confidence = (int(fqdn.confidence) / 2)
    fqdn.rdata = i.indicator

    return fqdn
