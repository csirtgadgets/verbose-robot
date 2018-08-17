import arrow
from csirtg_indicator import Indicator


def process(i):
    if i.itype not in ['ipv4', 'ipv6']:
        return

    if 'whitelist' not in i.tags:
        return

    if i.indicator.endswith('/24'):
        return

    prefix = i.indicator.split('.')
    prefix = prefix[:3]
    prefix.append('0/24')
    prefix = '.'.join(prefix)

    ii = Indicator(**i.__dict__())
    ii.probability = 0
    ii.lasttime = arrow.utcnow()

    ii.indicator = prefix
    ii.tags = ['whitelist']

    ii.confidence = 2

    return ii
