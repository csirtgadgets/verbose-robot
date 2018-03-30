import arrow

from csirtg_indicator import Indicator

ENABLED = False

try:
    from csirtg_domainsml import predict
    from csirtg_domainsml.constants import VERSION
    ENABLED = True
except:
    pass


def process(i):
    if not ENABLED:
        return

    if i.itype != 'fqdn':
        return

    if i.probability:
        return

    for t in i.tags:
        if t == 'predicted':
            return

    if not predict(i.indicator):
        return

    fqdn = Indicator(**i.__dict__())
    fqdn.lasttime = arrow.utcnow()
    fqdn.confidence = 9
    fqdn.probability = 84
    fqdn.provider = 'csirtgadgets.com'
    fqdn.reference = 'https://github.com/csirtgadgets/csirtg-domainsml-py' + '#' + VERSION
    tags = set(fqdn.tags)
    tags.add('predicted')
    fqdn.tags = list(tags)

    return fqdn
