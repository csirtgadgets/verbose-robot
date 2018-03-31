import arrow

from csirtg_indicator import Indicator
ENABLED = False

try:
    from csirtg_urlsml import predict
    from csirtg_urlsml.constants import VERSION
    ENABLED = True
except:
    pass


def process(i):
    if not ENABLED:
        return

    if i.itype != 'url':
        return

    if i.probability:
        return

    for t in i.tags:
        if t == 'predicted':
            return

    if not predict(i.indicator):
        return

    i = Indicator(**i.__dict__())
    i.lasttime = arrow.utcnow()
    i.confidence = 4
    i.probability = 84
    i.provider = 'csirtgadgets.com'
    i.reference = 'https://github.com/csirtgadgets/csirtg-urlsml-py' + '#' + VERSION

    tags = set(i.tags)
    tags.add('predicted')
    i.tags = list(tags)

    return i
