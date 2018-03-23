#!/usr/bin/env python

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from cifsdk.constants import REMOTE_ADDR, CONFIG_PATH
from cifsdk.utils import setup_logging, get_argument_parser, read_config
from cifsdk.utils.zarrow import parse_timestamp
from cifsdk.exceptions import AuthError
from prettytable import PrettyTable
import arrow
import yaml
from pprint import pprint

TOKEN = os.getenv('CIF_TOKEN', None)
COLS = os.getenv('CIF_TOKEN_COLUMNS', ['username', 'groups', 'last_activity_at', 'admin', 'read', 'write', 'acl',
                                       'expires', 'token'])


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        example usage:
            $ cif-tokens --name wes@csirtgadgets.org --create --admin
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='cif',
        parents=[p]
    )

    p.add_argument('--token', help='specify api token [default %(default)s]', default=TOKEN)
    p.add_argument('--remote', help='specify API remote [default %(default)s]', default=REMOTE_ADDR)

    p.add_argument('--create', help='create token (requires admin token', action='store_true')
    p.add_argument('--delete', help='delete token (requires admin token)', action='store_true')
    p.add_argument('--delete-token', help='specify the token to delete')

    p.add_argument('--username', help='specify username')
    p.add_argument('--name', help='specify username')

    p.add_argument('--admin', action='store_true')
    p.add_argument('--expires', help='set a token expiration timestamp')
    p.add_argument('--read', help='set the token read flag', action='store_true')
    p.add_argument('--write', help='set the token write flag', action='store_true')
    p.add_argument('--revoked', help='set the token revoked flag', action='store_true')
    p.add_argument('--groups', help='specify token groups (eg: everyone,group1,group2) [default %(default)s]',
                   default='everyone')
    p.add_argument('--no-everyone', help="do not create key in the 'everyone' group", action='store_true')
    p.add_argument('--acl', help='set the token itype acls (eg: ipv4,ipv6)', default='')

    p.add_argument('--columns', help='specify columns to print when searching [default %(default)s]',
                   default=','.join(COLS))

    p.add_argument('--config-generate', help='generate configuration file')
    p.add_argument('--config', help='specify configuration file [default %(default)s]', default=CONFIG_PATH)
    p.add_argument('--no-verify-ssl', help='Turn OFF TLS verification', action='store_true')

    p.add_argument('--update', help='update a token')

    args = p.parse_args()

    setup_logging(args)
    logger = logging.getLogger(__name__)

    o = read_config(args)
    options = vars(args)

    if not options.get('token'):
        raise RuntimeError('missing --token')

    verify_ssl = True
    if o.get('no_verify_ssl') or options.get('no_verify_ssl'):
        verify_ssl = False

    options = vars(args)

    from cifsdk.client.http import HTTP as HTTPClient
    cli = HTTPClient(args.remote, args.token, verify_ssl=verify_ssl)

    if options.get('name'):
        options['username'] = options['name']

    rv = False
    if options.get('create'):
        if not options.get('username'):
            raise RuntimeError('missing --username')

        if not (options.get('read') or options.get('write')):
            logger.info('assuming --read token')
            options['read'] = True

        groups = set(options.get('groups').split(','))
        if not options.get('no_everyone'):
            if 'everyone' not in groups:
                groups.add('everyone')

        acl = options.get('acl').split(',')

        try:
            rv = cli.tokens_create({
                'username': options.get('username'),
                'admin': options.get('admin'),
                'expires': options.get('expires'),
                'read': options.get('read'),
                'revoked': options.get('revoked'),
                'write': options.get('write'),
                'groups': list(groups),
                'acl': acl
            })
        except AuthError as e:
            logger.error(e)
        except Exception as e:
            logger.error('token create failed: {}'.format(e))
        else:
            if options.get('config_generate'):
                data = {
                    'remote': options['remote'],
                    'token': str(rv['token']),
                }
                with open(options['config_generate'], 'w') as f:
                    f.write(yaml.dump(data, default_flow_style=False))

            t = PrettyTable(args.columns.split(','))
            l = []
            for c in args.columns.split(','):
                if c == 'last_activity_at' and rv.get(c):
                    rv[c] = arrow.get(rv[c]).format('YYYY-MM-DDTHH:MM:ss')
                    rv[c] = '{}Z'.format(rv[c])

                if c == 'expires' and rv.get(c):
                    rv[c] = arrow.get(rv[c]).format('YYYY-MM-DDTHH:MM:ss')
                    rv[c] = '{}Z'.format(rv[c])

                if rv.get(c):
                    if type(rv[c]) == list:
                        l.append(','.join(rv[c]))
                    else:
                        l.append(str(rv[c]))
                else:
                    l.append(None)
            t.add_row(l)
            print(t)

    elif options.get('delete_token'):
        try:
            rv = cli.tokens_delete({
                'token': options.get('delete_token'),
                'username': options.get('username')
            })
            if rv:
                logger.info('deleted: {} tokens successfully'.format(rv))
            else:
                logger.error('no tokens deleted')
        except Exception as e:
            logger.error('token delete failed: %s' % e)

    elif options.get('delete'):
        if not (options.get('delete_token') or options.get('username')):
            raise RuntimeError('--delete requires --delete-token or --username')
        try:
            rv = cli.tokens_delete({
                'token': options.get('delete_token'),
                'username': options.get('username')
            })
            if rv:
                logger.info('deleted: {} tokens successfully'.format(rv))
            else:
                logger.error('no tokens deleted')
        except Exception as e:
            logger.error('token delete failed: %s' % e)
    elif options.get('update'):
        if not options.get('groups'):
            raise RuntimeError('requires --groups')

        groups = options['groups'].split(',')

        rv = cli.tokens_edit({
            'token': options['update'],
            'groups': groups
        })

        if rv:
            logger.info('token updated successfully')
            rv = cli.tokens_search({'token': options['update']})
            t = PrettyTable(args.columns.split(','))
            for r in rv:
                l = []
                for c in args.columns.split(','):
                    if c == 'last_activity_at' and r[c] is not None:
                        r[c] = arrow.get(r[c]).format('YYYY-MM-DDTHH:MM:ss')
                        r[c] = '{}Z'.format(r[c])
                    if c == 'expires' and r[c] is not None:
                        r[c] = arrow.get(r[c]).format('YYYY-MM-DDTHH:MM:ss')
                        r[c] = '{}Z'.format(r[c])
                    l.append(r[c])
                t.add_row(l)
            print(t)
        else:
            logger.error(rv)
    else:
        filters = {}
        if options.get('username'):
            filters['username'] = options.get('username')
        try:
            rv = cli.tokens_search(filters)
        except AuthError:
            logger.error('unauthorized')
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("\ntoken search failed: %s" % e)
        else:
            t = PrettyTable(args.columns.split(','))
            for r in rv:
                l = []
                for c in args.columns.split(','):
                    if c == 'last_activity_at' and r.get(c) is not None:
                        r[c] = parse_timestamp(r[c]).format('YYYY-MM-DDTHH:mm:ss.SS')
                        r[c] = '{}Z'.format(r[c])
                    if c == 'expires' and r.get(c) is not None:
                        r[c] = parse_timestamp(r[c]).format('YYYY-MM-DDTHH:mm:ss.SS')
                        r[c] = '{}Z'.format(r[c])
                    if type(r.get(c)) == list:
                        r[c] = ','.join(r[c])
                    l.append(r.get(c))
                t.add_row(l)
            print(t)


if __name__ == "__main__":
    main()
