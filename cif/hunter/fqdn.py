import arrow
import os
from pprint import pprint

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', True)


def process(i):
    if not ENABLED or not i.is_fqdn:
        return

    if 'pdns' in i.tags:
        return

    # if i.get("rdata", '') != '' and not i.get('rdata').startswith('http'):
    #     return

    i.fqdn_resolve()

    if i.get("rdata", '') == '':
        return

    for r in i.rdata:
        ip = i.copy(**{'indicator': r, 'last_at': arrow.utcnow()})
        ip.rdata = [i.indicator]
        ip.fqdn_resolve()
        ip.geo_resolve()
        ip.confidence = 0
        if i.confidence > 0:
            ip.confidence = i.confidence - 1

        pdns = ip.copy(tags=['pdns'], confidence=4.0, rdata=[i.indicator])

        yield ip
        yield pdns


def main():
    import logging

    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)

    from csirtg_indicator import Indicator
    i = Indicator('csirtg.io', confidence=2, tags='phishing')
    rv = process(i)

    for r in rv:
        print(str(r))


if __name__ == '__main__':
    main()
