from flask import request, jsonify
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


def jsonify_unauth(msg='unauthorized'):
    response = jsonify({
        "message": msg,
        "data": []
    })
    response.status_code = 401
    return response


def jsonify_unknown(msg='failed', code=503):
    response = jsonify({
        "message": msg,
        "data": []
    })
    response.status_code = code
    return response


def jsonify_busy(msg='system is busy, try again later', code=503):
    response = jsonify({
        'message': msg,
        'data': [],
    })
    response.status_code = code
    return response


def jsonify_success(data=[], code=200):
    response = jsonify({
        'message': 'success',
        'data': data
    })
    response.status_code = code
    return response


def aggregate(data, field='indicator', sort='confidence', sort_secondary='reporttime'):
    x = set()
    rv = []
    for d in sorted(data, key=lambda x: x[sort], reverse=True):
        if d[field] not in x:
            x.add(d[field])
            rv.append(d)

    rv = sorted(rv, key=lambda x: x[sort_secondary], reverse=True)
    return rv
