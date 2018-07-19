import arrow

from csirtg_indicator import Indicator
ENABLED = False

try:
    from csirtg_urlsml_tf import predict
    from csirtg_urlsml_tf.constants import VERSION
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

    p = predict(i.indicator)
    p = round((p[0][0] * 100), 2)

    if p < 80:
        return

    i = Indicator(**i.__dict__())
    i.lasttime = arrow.utcnow()
    i.confidence = 4
    i.probability = str(p)
    i.provider = 'csirtgadgets.com'
    i.reference = 'https://github.com/csirtgadgets/csirtg-urlsml-tf-py' + '#' + VERSION

    tags = set(i.tags)
    tags.add('predicted')
    i.tags = list(tags)

    return i
