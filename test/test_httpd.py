import json
import os
import tempfile

import pytest
from cif.httpd.app import app
from cif.store import Store


ROUTER_ADDR = 'ipc://{}'.format(tempfile.NamedTemporaryFile().name)

@pytest.fixture
def client(request):
    app.config['TESTING'] = True
    app.config['CIF_ROUTER_ADDR'] = ROUTER_ADDR
    app.config['dummy'] = True
    return app.test_client()


@pytest.yield_fixture
def store():
    dbfile = tempfile.mktemp()
    with Store(store_type='sqlite', dbfile=dbfile) as s:
        yield s

    os.unlink(dbfile)


def test_httpd_help(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_httpd_ping(client):
    rv = client.get('/ping/')
    assert rv.status_code == 401

    rv = client.get('/ping/', headers={'Authorization': '1234'})
    assert rv.status_code == 200


def test_httpd_search(client):
    rv = client.get('/indicators/?q=example.com', headers={'Authorization': '1234'})
    assert rv.status_code == 200

    data = rv.data

    rv = json.loads(data.decode('utf-8'))
    assert rv['data'][0]['indicator'] == 'example.com'


def test_httpd_tokens(client):
    rv = client.get('/tokens/', headers={'Authorization': '1234'})
    assert rv.status_code == 200


def test_httpd_graph(client):
    rv = client.get('/graph/', headers={'Authorization': '1234'})
    assert rv.status_code == 200
