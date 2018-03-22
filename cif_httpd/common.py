from flask import request
import re


def pull_token():
    t = None
    if request.headers.get("Authorization"):
        t = re.match("^Token token=(\S+)$", request.headers.get("Authorization"))
        if t:
            t = t.group(1)
    return t


def request_v3():
    if request.headers.get('Accept'):
        if 'vnd.cif.v3+json' in request.headers['Accept']:
            return True


def aggregate(data, field='indicator', sort='confidence', sort_secondary='reporttime'):
    x = set()
    rv = []
    for d in sorted(data, key=lambda x: x[sort], reverse=True):
        if d[field] not in x:
            x.add(d[field])
            rv.append(d)

    rv = sorted(rv, key=lambda x: x[sort_secondary], reverse=True)
    return rv
