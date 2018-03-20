import logging
import os
import geoip2.database
import pygeoip
from geoip2.errors import AddressNotFoundError
import re
from csirtg_indicator import Indicator
from cif.constants import PYVERSION
from cifsdk.utils.network import resolve_fqdn, resolve_url
from pprint import pprint


DB_SEARCH_PATHS = [
    './',
    '/usr/share/GeoIP',
    '/usr/local/share/GeoIP'
]

ENABLE_FQDN = os.getenv('CIF_GATHERER_GEO_FQDN')
DB_FILE = 'GeoLite2-City.mmdb'
DB_PATH = os.environ.get('CIF_GEO_PATH')

ASN_DB_PATH = 'GeoIPASNum.dat'
ASN_DB_PATH2 = 'GeoLiteASNum.dat'
CITY_DB_PATH = 'GeoLiteCity.dat'
CITY_V6_DB_PATH = 'GeoLiteCityv6.dat'

DB = None
ASN_DB = None
CITY_DB = None
CITY_V6_DB = None

if DB_PATH:
    DB = geoip2.database.Reader(os.path.join(DB_PATH, DB_FILE))
else:
    for p in DB_SEARCH_PATHS:
        if os.path.isfile(os.path.join(p, DB_FILE)):
            DB = geoip2.database.Reader(os.path.join(p, DB_FILE))
            break

for p in DB_SEARCH_PATHS:
    if os.path.isfile(os.path.join(p, ASN_DB_PATH)):
        ASN_DB = pygeoip.GeoIP(os.path.join(p, ASN_DB_PATH), pygeoip.MMAP_CACHE)
        break

    if os.path.isfile(os.path.join(p, ASN_DB_PATH2)):
        ASN_DB = pygeoip.GeoIP(os.path.join(p, ASN_DB_PATH2), pygeoip.MMAP_CACHE)
        break

for p in DB_SEARCH_PATHS:
    if os.path.isfile(os.path.join(p, CITY_DB_PATH)):
        CITY_DBY = pygeoip.GeoIP(os.path.join(p, CITY_DB_PATH), pygeoip.MMAP_CACHE)
        break

    if os.path.isfile(os.path.join(p, CITY_V6_DB_PATH)):
        CITY_DB_PATH = pygeoip.GeoIP(os.path.join(p, CITY_V6_DB_PATH), pygeoip.MMAP_CACHE)


def _ip_to_prefix(i):
    i = list(i.split('.'))
    i = '{}.{}.{}.0'.format(i[0], i[1], i[2])
    return str(i)


def _resolve(indicator):
    if not DB:
        return

    i = indicator.indicator
    if indicator.itype in ['url', 'fqdn']:
        if ENABLE_FQDN in ['0', 0, False, None]:
            return

        if indicator.itype == 'url':
            i = resolve_url(i)

        i = resolve_fqdn(i)
        if not i:
            return

        if not indicator.rdata:
            indicator.rdata = i

    if indicator.itype == 'ipv4':
        try:
            i = _ip_to_prefix(i)
        except IndexError:
            return

    g = DB.city(i)

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

    g = CITY_DB.record_by_addr(i)

    if g and g.get('region_code'):
        indicator.region = g['region_code']

    g = ASN_DB.asn_by_addr(i)
    if g:
        m = re.match('^AS(\d+)\s([^.]+)', g)
        if m:
            indicator.asn = m.group(1)
            indicator.asn_desc = m.group(2)


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
    except AddressNotFoundError as e:
        indicator.indicator = tmp

    return indicator
