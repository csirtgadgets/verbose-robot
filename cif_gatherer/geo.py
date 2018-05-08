import logging
import os
import geoip2.database
import re
from csirtg_indicator import Indicator
from pprint import pprint
import sys
from cifsdk.utils.network import resolve_fqdn, resolve_url

# more local first, see search path loop
DB_SEARCH_PATHS = [
    '/usr/share/GeoIP',
    '/usr/local/share/GeoIP',
    '/usr/local/var/GeoIP',
    './',
]

ENABLE_FQDN = os.getenv('CIF_GATHERER_GEO_FQDN')
CITY_DB_PATH = 'GeoLite2-City.mmdb'
ASN_DB_PATH = 'GeoLite2-ASN.mmdb'

logger = logging.getLogger('cif.gatherer')

for p in DB_SEARCH_PATHS:
    if os.path.isfile(os.path.join(p, CITY_DB_PATH)):
        CITY_DB = geoip2.database.Reader(os.path.join(p, CITY_DB_PATH))

    if os.path.isfile(os.path.join(p, ASN_DB_PATH)):
        ASN_DB = geoip2.database.Reader(os.path.join(p, ASN_DB_PATH))


def _resolve(indicator):
    if not CITY_DB:
        return

    i = indicator.indicator

    if indicator.itype in ['url', 'fqdn']:
        if not ENABLE_FQDN:
            return

        if indicator.itype == 'url':
            i = resolve_url(i)

        i = resolve_fqdn(i)
        if not i:
            return

        if not indicator.rdata:
            indicator.rdata = i

    g = CITY_DB.city(i)

    if g.country.iso_code:
        indicator.cc = g.country.iso_code

    if g.city.name:
        indicator.city = g.city.name

    if g.location.longitude:
        indicator.longitude = g.location.longitude

    if g.location.latitude:
        indicator.latitude = g.location.latitude

    if g.location.latitude and g.location.longitude:
        indicator.location = [g.location.longitude, g.location.latitude]

    if g.location.time_zone:
        indicator.timezone = g.location.time_zone

    try:
        indicator.region = g.subdivisions[0].names['en']
    except Exception:
        pass

    g = ASN_DB.asn(i)

    if not g:
        return

    if g.autonomous_system_number:
        indicator.asn = g.autonomous_system_number

    if g.autonomous_system_organization:
        indicator.asn_desc = g.autonomous_system_organization


def process(indicator):
    if indicator.itype not in ['ipv4', 'ipv6', 'fqdn', 'url']:
        return indicator

    if indicator.is_private():
        return indicator

    # https://geoip2.readthedocs.org/en/latest/
    i = str(indicator.indicator)
    tmp = indicator.indicator

    if indicator.itype in ['ipv4', 'ipv6']:
        match = re.search('^(\S+)\/\d+$', i)
        if match:
            indicator.indicator = match.group(1)

    try:
        if indicator.indicator:
            _resolve(indicator)
        indicator.indicator = tmp
    except ValueError as e:
        indicator.indicator = tmp

    return indicator


def main():
    i = sys.argv[1]

    i = Indicator(i)
    i = process(i)

    pprint(i)


if __name__ == "__main__":
    main()
