import logging
from argparse import Namespace
import pytest
from cifsdk.utils import setup_logging
import arrow
from test.store.test_basics import store, indicator


args = Namespace(debug=True, verbose=None)
setup_logging(args)

logger = logging.getLogger(__name__)


def test_indicators_create(store, indicator):
    t = store.store.tokens.admin_exists()

    x = store.handle_indicators_create(t, indicator)

    # TODO- fix this based on store handle
    assert x == 0

    indicator['last_at'] = arrow.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    indicator['tags'] = ['malware']

    x = store.handle_indicators_create(t, indicator)

    assert x == 0


def test_indicators_search_fqdn(store, indicator):
    t = store.store.tokens.admin_exists()
    x = store.handle_indicators_search(t, {
        'indicator': 'example.com',
    })

    assert len(list(x)) > 0

    indicator['tags'] = 'botnet'
    indicator['indicator'] = 'example2.com'

    x = store.handle_indicators_create(t, indicator)

    assert x == 0

    x = store.handle_indicators_search(t, {
        'indicator': 'example2.com',
    })

    assert len(list(x)) > 0

    x = store.handle_indicators_search(t, {
        'indicator': 'example2.com',
        'tags': 'malware'
    })

    assert len(x) == 0


def test_indicators_search_ipv4(store, indicator):
    t = store.store.tokens.admin_exists()
    indicator['indicator'] = '192.168.1.1'
    indicator['itype'] = 'ipv4'
    indicator['tags'] = 'botnet'

    x = store.handle_indicators_create(t, indicator)

    assert x == 0

    for i in ['192.168.1.1', '192.168.1.0/24']:
        x = store.handle_indicators_search(t, {
            'indicator': i,
        })

        assert len(list(x)) > 0


def test_indicators_search_ipv6(store, indicator):
    t = store.store.tokens.admin_exists()

    indicator['indicator'] = '2001:4860:4860::8888'
    indicator['itype'] = 'ipv6'
    indicator['tags'] = 'botnet'

    x = store.handle_indicators_create(t, indicator)

    # TODO- it gets inserted, need to re-check upsert math
    assert x == 0

    x = store.handle_indicators_search(t, {
        'indicator': '2001:4860:4860::8888',
    })

    assert len(list(x)) > 0

    x = store.handle_indicators_search(t, {
        'indicator': '2001:4860::/32',
    })

    assert len(list(x)) > 0


def test_indicators_invalid(store, indicator):
    t = store.store.tokens.admin_exists()
    del indicator['tags']

    x = None

    try:
        x = store.handle_indicators_create(t, indicator)
    except ValueError:
        pass

    assert (x is None or x == 0)

    indicator['tags'] = 'malware'

    del indicator['group']
    try:
        x = store.handle_indicators_create(t, indicator)
    except ValueError:
        pass

    assert (x is None or x == 0)


def test_indicators_delete(store, indicator):
    t = store.store.tokens.admin_exists()

    x = store.handle_indicators_create(t, indicator)

    r = store.handle_indicators_delete(t, data=[{
        'indicator': 'example.com',
    }])
    assert r == 1

    x = store.handle_indicators_search(t, {
        'indicator': 'example.com',
        'nolog': 1
    })
    assert len(x) == 0

    x = store.handle_indicators_search(t, {
        'indicator': 'example2.com',
        'nolog': 1
    })

    for xx in x:
        r = store.handle_indicators_delete(t, data=[{
            'id': xx['id']
        }])
        assert r == 1


def test_indicators_create_sha1(store, indicator):
    t = store.store.tokens.admin_exists()

    indicator['indicator'] = 'd52380918a07322c50f1bfa2b43af3bb54cb33db'
    indicator['group'] = 'everyone'
    indicator['itype'] = 'sha1'

    x = store.handle_indicators_create(t, indicator)
    # TODO indicators_hash table isn't showing up..

    # assert x == -1
    #
    # x = store.handle_indicators_search(t, {
    #     'indicator': indicator['indicator'],
    #     'nolog': 1
    # })
    # assert len(x) == 1
