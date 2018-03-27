import arrow

from csirtg_indicator import Indicator

try:
    from csirtg_domainsml import predict
except:
    pass


def process(i):
    return

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
