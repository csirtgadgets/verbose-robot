import arrow

from csirtg_indicator import Indicator
try:
    from csirtg_urlsml import predict
except:
    pass


def process(i):
    if i.itype != 'url':
        return

    if not predict(i.indicator):
        return

    i = Indicator(**i.__dict__())
    i.lasttime = arrow.utcnow()
    i.confidence = 9
    i.probability = 9
    i.provider = 'csirtgadgets.com'
    i.tags.append('predicted')
    i.reference = 'https://github.com/csirtgadgets/csirtg-urlsml-py'

    return i
