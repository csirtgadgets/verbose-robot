
import logging
import os
import tempfile
from argparse import Namespace
import pytest
from cif.store import Store
from cifsdk.utils import setup_logging
import arrow
from datetime import datetime

args = Namespace(debug=True, verbose=None)
setup_logging(args)

logger = logging.getLogger(__name__)


@pytest.yield_fixture
def store():
    dbfile = tempfile.mktemp()
    with Store(store_type='sqlite', dbfile=dbfile) as s:
        s.token_handler.token_create_admin()
        yield s

    if os.path.isfile(dbfile):
        os.unlink(dbfile)


def test_tokens(store):
    t = store.store.tokens.admin_exists()
    assert t

    t = list(store.store.tokens.search({'token': t}))
    assert len(t) > 0

    t = t[0]['token']

    assert store.store.tokens.update_last_activity_at(t, datetime.now())
    assert store.store.tokens.check(t, 'read')
    assert store.store.tokens.read(t)
    assert store.store.tokens.write(t)
    assert store.store.tokens.admin(t)
    assert store.store.tokens.last_activity_at(t) is not None
    assert store.store.tokens.update_last_activity_at(t, datetime.now())
