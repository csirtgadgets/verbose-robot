import arrow

from csirtg_indicator import Indicator

ENABLED = False

try:
    from csirtg_domainsml_tf import predict
    from csirtg_domainsml_tf.constants import VERSION
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

    p = predict(i.indicator)
    p = round((p[0][0] * 100), 2)

    if p < 80:
        return

    fqdn = Indicator(**i.__dict__())
    fqdn.lasttime = arrow.utcnow()
    fqdn.confidence = 4
    fqdn.probability = str(p)
    fqdn.provider = 'csirtgadgets.com'
    fqdn.reference = 'https://github.com/csirtgadgets/csirtg-domainsml-tf-py' + '#' + VERSION
    tags = set(fqdn.tags)
    tags.add('predicted')
    fqdn.tags = list(tags)

    return fqdn
