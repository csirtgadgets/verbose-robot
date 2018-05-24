from csirtg_indicator import Indicator, resolve_itype
import arrow


def process(i):
    if i.itype != 'fqdn':
        return

    if not i.is_subdomain():
        return

    fqdn = Indicator(**i.__dict__())
    fqdn.probability = 0
    fqdn.indicator = i.is_subdomain()
    fqdn.lasttime = arrow.utcnow()

    try:
        resolve_itype(fqdn.indicator)
    except:
        return

    fqdn.confidence = 1
    return fqdn
