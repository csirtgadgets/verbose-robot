#!/usr/bin/env python

import logging
import select
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from cifsdk.constants import REMOTE_ADDR, TOKEN, SEARCH_LIMIT, FORMAT, COLUMNS
from cifsdk.exceptions import AuthError
from csirtg_indicator.format import FORMATS
from cifsdk.utils import setup_logging, get_argument_parser
from csirtg_indicator import Indicator
from cifsdk.client.http import HTTP as Client

logger = logging.getLogger(__name__)


def _search(cli, args, options, filters):

    try:
        rv = cli.search(filters)

    except AuthError as e:
        logger.error('unauthorized')

    except KeyboardInterrupt:
        pass

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(e)

    else:
        print(FORMATS[options.get('format')](data=rv, cols=args.columns.split(',')))

    raise SystemExit


def _ping(cli, args):
    logger.info('running ping')
    n = 4
    if args.ping_indef:
        n = 999

    try:
        for num in range(0, n):
            ret = cli.ping()
            if ret != 0:
                print("roundtrip: {} ms".format(ret))
                select.select([], [], [], 1)
                from time import sleep
                sleep(1)
            else:
                logger.error('ping failed')
                raise RuntimeError
    except KeyboardInterrupt:
        pass
    raise SystemExit


def _submit(cli, args, options):
    print("submitting {0}".format(options.get("submit")))
    i = Indicator(indicator=args.indicator, tags=args.tags, confidence=args.confidence)
    rv = cli.indicators_create(i)

    print('success id: {}\n'.format(rv))
    raise SystemExit


def _delete(cli, args, filters):
    if args.id:
        filters = {'id': args.id}

    filters = {f: filters[f] for f in filters if filters.get(f)}
    print("deleting {0}".format(filters))
    rv = cli.indicators_delete(filters)

    print('deleted: {}'.format(rv))
    raise SystemExit


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        example usage:
            $ cif -q example.org -d
            $ cif --search 1.2.3.0/24
            $ cif --ping
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif',
        parents=[p]
    )
    p.add_argument('--token', help='specify api token', default=TOKEN)
    p.add_argument('--remote', help='specify API remote [default %(default)s]', default=REMOTE_ADDR)
    p.add_argument('--no-verify-ssl', action='store_true')

    p.add_argument('-p', '--ping', action="store_true")
    p.add_argument('--ping-indef', action="store_true")
    p.add_argument("--submit", action="store_true", help="submit an indicator")
    p.add_argument('--delete', action='store_true')
    p.add_argument('-q', '--search', help="search")

    p.add_argument('--id')
    p.add_argument('--itype', help='filter by indicator type')
    p.add_argument('--reported_at', help='specify reported_at filter')
    p.add_argument('-n', '--nolog', help='do not log search', action='store_true')
    p.add_argument('-f', '--format', help='specify output format [default: %(default)s]"', default=FORMAT, choices=FORMATS.keys())
    p.add_argument('--indicator')
    p.add_argument('--confidence', help="specify confidence level")
    p.add_argument('--probability')
    p.add_argument('--tags', nargs='+')
    p.add_argument('--provider')
    p.add_argument('--asn')
    p.add_argument('--cc')
    p.add_argument('--asn-desc')
    p.add_argument('--rdata')
    p.add_argument('--region')
    p.add_argument('--groups', help='specify groups filter (csv)')

    p.add_argument('--days', help='filter results within last X days')
    p.add_argument('--today', help='auto-sets reporttime to today, 00:00:00Z (UTC)', action='store_true')

    p.add_argument('--limit', help='limit results [default %(default)s]', default=SEARCH_LIMIT)
    p.add_argument('--columns', help='specify output columns [default %(default)s]', default=','.join(COLUMNS))
    p.add_argument('--no-feed', action='store_true')

    args = p.parse_args()

    setup_logging(args)

    opts = vars(args)

    options = {}
    for k, v in opts.items():
        if v:
            options[k] = v

    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    if args.remote == 'https://localhost':
        verify_ssl = False

    cli = Client(args.remote, args.token, verify_ssl=verify_ssl)

    if args.ping or args.ping_indef:
        _ping(args)

    if options.get("submit"):
        _submit(cli, args)

    filters = {
        'itype': options.get('itype'),
        'limit': options.get('limit'),
        'provider': options.get('provider'),
        'indicator': options.get('search') or options.get('indicator'),
        'nolog': options.get('nolog'),
        'tags': options.get('tags'),
        'confidence': options.get('confidence'),
        'asn': options.get('asn'),
        'asn_desc': options.get('asn_desc'),
        'cc': options.get('cc'),
        'region': options.get('region'),
        'rdata': options.get('rdata'),
        'reported_at': options.get('reported_at'),
        'groups': options.get('groups'),
        'hours': options.get('hours'),
        'days': options.get('days'),
        'today': options.get('today'),
        'nofeed': options.get('nofeed'),
        'probability': options.get('probability')
    }

    for k, v in filters.items():
        if v is True:
            filters[k] = 1
        if v is False:
            filters[k] = 0

    if options.get("delete"):
        _delete(cli, args, options, filters)

    _search(cli, args, options, filters)


if __name__ == "__main__":
    main()
