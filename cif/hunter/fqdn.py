import arrow
import os, re
from pprint import pprint

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', True)


def process(i):
    if not ENABLED:
        return

    if not i.is_fqdn():
        return

    if 'pdns' in i.tags:
        return

    i.fqdn_resolve()

    if i.get("rdata", '') == '':
        return

    for r in i.rdata:
        ip = i.copy(**{'indicator': r, 'last_at': arrow.utcnow()})
        if ip is None:
            continue

        ip.rdata = [i.indicator]
        ip.fqdn_resolve()
        ip.geo_resolve()
        ip.confidence = 0
        if i.confidence > 0:
            ip.confidence = i.confidence - 1

        if not ip.description:
            ip.description = i.tags[0]

        # this could be a url too, the var is mis-leading
        yield ip

        if ip.is_ip():
            pdns = ip.copy(tags=['pdns'], confidence=4.0, rdata=[i.indicator])
            yield pdns

    for ns in i.get('ns', []):
        ns = ns.rstrip('.')
        i2 = i.copy(**{
            'indicator': ns,
            'confidence': 0,
            'count': 1,
            'ns': None,
            'mx': None,
            'rdata': None
        })
        if i2 is None:
            continue

        i2.fqdn_resolve()
        i2.geo_resolve()

        yield i2

        if i2.rdata:
            pdns = i2.copy(tags=['pdns'], confidence=4.0,
                           indicator=i2.rdata[0], rdata=ns)
            yield pdns

    for mx in i.get('mx', []):
        mx = re.sub(r'^\d+ ', '', mx)
        mx = mx.rstrip('.')
        i2 = i.copy(**{
            'indicator': mx,
            'confidence': 0,
            'count': 1,
            'ns': None,
            'mx': None,
            'rdata': None
        })
        if i2 is None:
            continue
        i2.fqdn_resolve()
        i2.geo_resolve()

        yield i2

    for r in i.get('cname', []):
        r = r.rstrip('.')
        i2 = i.copy(**{
            'indicator': r,
            'confidence': 0,
            'count': 1,
            'ns': None,
            'mx': None,
            'rdata': None
        })
        if i2 is None:
            continue
        i2.fqdn_resolve()
        i2.geo_resolve()

        yield i2


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
