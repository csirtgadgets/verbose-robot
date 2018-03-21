import arrow

from csirtg_indicator import Indicator
from csirtg_domainsml import predict


def process(i):
    if i.itype != 'fqdn':
        return

    if not predict(i.indicator):
        return

    fqdn = Indicator(**i.__dict__())
    fqdn.lasttime = arrow.utcnow()
    fqdn.confidence = 9
    fqdn.probability = 9
    fqdn.provider = 'csirtgadgets.com'
    fqdn.reference = 'https://github.com/csirtgadgets/csirtg-urlsml-py'
    fqdn.tags.append('predicted')

    return fqdn
