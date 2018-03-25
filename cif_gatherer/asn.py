import logging
import os
import re

from cifsdk.utils.network import resolve_ns

ENABLE_PEERS = os.getenv('CIF_GATHERERS_PEERS_ENABLED', False)


def _resolve(data):
    return resolve_ns('{}.{}'.format(data, 'origin.asn.cymru.com'), t='TXT')


def process(indicator):
    if not ENABLE_PEERS:
        return

    if indicator.is_private():
        return

    # TODO ipv6
    if indicator.itype != 'ipv4':
        return

    i = str(indicator.indicator)
    match = re.search('^(\S+)\/\d+$', i)
    if match:
        i = match.group(1)

    # cache it to the /24
    # 115.87.213.115
    # 0.213.87.115
    i = list(reversed(i.split('.')))
    i = '0.{}.{}.{}'.format(i[1], i[2], i[3])

    answers = _resolve(i)

    if len(answers) == 0:
        return

    # Separate fields and order by netmask length
    # 23028 | 216.90.108.0/24 | US | arin | 1998-09-25
    # 701 1239 3549 3561 7132 | 216.90.108.0/24 | US | arin | 1998-09-25

    # i.asn_desc ????
    bits = str(answers[0]).replace('"', '').strip().split(' | ')
    asns = bits[0].split(' ')

    indicator.asn = asns[0]
    indicator.prefix = bits[1]
    indicator.cc = bits[2]
    indicator.rir = bits[3]
    answers = resolve_ns('as{}.{}'.format(asns[0], 'asn.cymru.com'), t='TXT', timeout=15)

    try:
        tmp = str(answers[0])
    except UnicodeDecodeError as e:
        # requires fix latin-1 fix _escapeify to dnspython > 1.14
        return indicator
    except IndexError:
        return indicator

    bits = tmp.replace('"', '').strip().split(' | ')
    if len(bits) > 4:
        indicator.asn_desc = bits[4]

    # send back to router
    return indicator
